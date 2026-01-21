from __future__ import annotations
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler

from ..settings import BASE_DIR, load_config
from ..pipeline.build_dataset import load_jobs
from ..analytics.stats import city_top, salary_hist, tag_top
from ..analytics.trends import trend_by_date, tag_trend
from ..analytics.recommend import UserQuery, recommend
from ..viz.charts_pyecharts import bar_city, line_trend, wordcloud_tags
from ..viz.render import render_chart
from ..crawler.run_crawl import crawl_once

# 配置 Flask 应用路径
template_dir = BASE_DIR / "webapp" / "templates"
static_dir = BASE_DIR / "webapp" / "static"

app = Flask(__name__, template_folder=str(template_dir), static_folder=str(static_dir))

# 添加错误处理器
@app.errorhandler(500)
def internal_error(error):
    from ..utils.log import get_logger
    logger = get_logger(__name__)
    logger.error(f"Internal Server Error: {error}")
    return "Internal Server Error: 请查看服务器日志了解详细信息", 500

@app.errorhandler(Exception)
def handle_exception(e):
    from ..utils.log import get_logger
    logger = get_logger(__name__)
    logger.error(f"未处理的异常: {e}", exc_info=True)
    return f"错误: {str(e)}", 500

def build_charts():
    try:
        cfg = load_config()
        days = int(cfg.get("app", {}).get("data_days_window", 30))
        df = load_jobs(days=days)
        
        # 检查数据是否为空
        if len(df) == 0:
            from ..utils.log import get_logger
            logger = get_logger(__name__)
            logger.warning("没有数据，返回空 DataFrame")
            return df

        c_city = bar_city(city_top(df, 20))
        c_trend = line_trend(trend_by_date(df))
        c_tags = wordcloud_tags(tag_top(df, 50))

        charts_dir = BASE_DIR / "webapp" / "static" / "charts"
        charts_dir.mkdir(parents=True, exist_ok=True)
        
        render_chart(c_city, str(charts_dir / "city_top.html"))
        render_chart(c_trend, str(charts_dir / "trend.html"))
        render_chart(c_tags, str(charts_dir / "tags_wc.html"))

        return df
    except Exception as e:
        from ..utils.log import get_logger
        logger = get_logger(__name__)
        logger.error(f"构建图表失败: {e}", exc_info=True)
        import pandas as pd
        return pd.DataFrame()  # 返回空 DataFrame

@app.get("/")
def index():
    return render_template("index.html")

@app.get("/dashboard")
def dashboard():
    try:
        df = build_charts()
        # 检查是否有数据
        has_data = len(df) > 0
        return render_template(
            "dashboard.html",
            city_chart="charts/city_top.html",
            trend_chart="charts/trend.html",
            tags_chart="charts/tags_wc.html",
            has_data=has_data,
        )
    except Exception as e:
        from ..utils.log import get_logger
        logger = get_logger(__name__)
        logger.error(f"Dashboard 页面错误: {e}", exc_info=True)
        return render_template(
            "dashboard.html",
            city_chart="charts/city_top.html",
            trend_chart="charts/trend.html",
            tags_chart="charts/tags_wc.html",
            has_data=False,
            error_message=str(e),
        ), 500

@app.route("/api/autocomplete", methods=["GET"])
def autocomplete_data():
    """获取自动完成数据（城市和技能关键词）"""
    try:
        cfg = load_config()
        days = int(cfg.get("app", {}).get("data_days_window", 30))
        df = load_jobs(days=days)
        
        # 获取城市列表
        cities = []
        if len(df) > 0 and "city" in df.columns:
            cities = df["city"].fillna("").dropna().unique().tolist()
            cities = [c for c in cities if c and c.strip() and c != "Unknown"]
            cities = sorted(set(cities))[:50]  # 限制数量并排序
        
        # 获取技能关键词列表（从tags字段）
        skills = []
        if len(df) > 0 and "tags" in df.columns:
            import json
            from collections import Counter
            c = Counter()
            for x in df["tags"].fillna("[]"):
                try:
                    arr = json.loads(x)
                    for t in arr:
                        if isinstance(t, str) and len(t.strip()) > 0:
                            c[t.strip().lower()] += 1
                except Exception:
                    continue
            skills = [skill for skill, count in c.most_common(100)]
        
        return jsonify({
            "cities": cities,
            "skills": skills
        })
    except Exception as e:
        from ..utils.log import get_logger
        logger = get_logger(__name__)
        logger.error(f"获取自动完成数据失败: {e}", exc_info=True)
        return jsonify({"cities": [], "skills": []}), 500

@app.route("/recommend", methods=["GET", "POST"])
def recommend_page():
    try:
        cfg = load_config()
        days = int(cfg.get("app", {}).get("data_days_window", 30))
        topn = int(cfg.get("app", {}).get("topn", 20))
        w_sim = float(cfg.get("recommend", {}).get("weight_similarity", 0.75))
        w_sal = float(cfg.get("recommend", {}).get("weight_salary", 0.25))

        df = load_jobs(days=days)
        rows = []
        form_data = {}  # 保存表单数据以便在页面中回显
        
        if request.method == "POST":
            # 保存表单数据
            form_data = {
                "city": request.form.get("city") or "",
                "min_salary": request.form.get("min_salary") or "",
                "max_exp": request.form.get("max_exp") or "",
                "education": request.form.get("education") or "",
                "keyword": request.form.get("keyword") or "",
                "skills": request.form.get("skills") or "",
            }
            
            q = UserQuery(
                city=form_data["city"] or None,
                min_salary=int(form_data["min_salary"]) if form_data["min_salary"] else None,
                education=form_data["education"] or None,
                max_exp_years=int(form_data["max_exp"]) if form_data["max_exp"] else None,
                skills_text=form_data["skills"] or "",
                keyword=form_data["keyword"] or None,
            )
            try:
                rec = recommend(df, q, topk=topn, w_sim=w_sim, w_sal=w_sal)
                
                # 检查是否有结果
                if len(rec) > 0:
                    # 选择需要的列
                    columns = ["title", "company", "city", "salary_raw", "detail_url", "score"]
                    # 只选择存在的列
                    available_columns = [col for col in columns if col in rec.columns]
                    rows = rec[available_columns].to_dict("records")
                # 如果 rec 为空（len(rec) == 0），rows 保持为空列表，这是正确的
            except Exception as e:
                from ..utils.log import get_logger
                logger = get_logger(__name__)
                logger.error(f"推荐功能出错: {e}")
                rows = []  # 出错时返回空列表
        return render_template("recommend.html", rows=rows, form_data=form_data)
    except Exception as e:
        from ..utils.log import get_logger
        logger = get_logger(__name__)
        logger.error(f"推荐页面错误: {e}", exc_info=True)
        from flask import abort
        abort(500)

@app.route("/crawl", methods=["POST"])
def crawl_now():
    try:
        keyword = request.form.get("keyword") or "python"
        city = request.form.get("city") or ""
        platform = request.form.get("platform") or "remoteok"
        
        # 验证平台参数
        if platform not in ["remoteok", "job51"]:
            platform = "remoteok"
        
        # web应用一次采集数据采集10页
        result = crawl_once(keyword=keyword, city=city or None, pages=10, platform=platform)
        
        # 返回详细的JSON响应
        return jsonify({
            "success": True,
            "message": f"成功采集 {result['count']} 条岗位数据",
            "data": result
        }), 200
    except Exception as e:
        from ..utils.log import get_logger
        logger = get_logger(__name__)
        logger.error(f"数据采集失败: {e}", exc_info=True)
        return jsonify({
            "success": False,
            "message": f"采集失败: {str(e)}",
            "error": str(e)
        }), 500

def start_scheduler():
    cfg = load_config()
    keyword = cfg.get("crawler", {}).get("default_keyword", "python")
    platform = cfg.get("crawler", {}).get("default_platform", "remoteok")
    sched = BackgroundScheduler(daemon=True)
    # Every day at 09:00 local time (you can adjust)
    def scheduled_crawl():
        try:
            result = crawl_once(keyword=keyword, city=None, pages=1, platform=platform)
            from ..utils.log import get_logger
            logger = get_logger(__name__)
            logger.info(f"定时采集完成: {result['count']} 条岗位 (平台={platform})")
        except Exception as e:
            from ..utils.log import get_logger
            logger = get_logger(__name__)
            logger.error(f"定时采集失败: {e}", exc_info=True)
    sched.add_job(scheduled_crawl, "cron", hour=9, minute=0)
    sched.start()

if __name__ == "__main__":
    start_scheduler()
    app.run(debug=True)
