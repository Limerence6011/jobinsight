from __future__ import annotations
from pathlib import Path
import os
import json
from collections import Counter
from functools import wraps

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.exceptions import HTTPException
from sqlalchemy.orm import Session
from apscheduler.schedulers.background import BackgroundScheduler

from ..settings import BASE_DIR, load_config
from ..pipeline.build_dataset import load_jobs
from ..analytics.stats import city_top, tag_top
from ..analytics.trends import trend_by_date
from ..analytics.recommend import UserQuery, recommend
from ..viz.charts_pyecharts import bar_city, line_trend, wordcloud_tags
from ..viz.render import render_chart
from ..crawler.run_crawl import crawl_once
from ..storage.db import ENGINE
from ..storage.models import User
from ..utils.log import get_logger

logger = get_logger(__name__)

template_dir = BASE_DIR / "webapp" / "templates"
static_dir = BASE_DIR / "webapp" / "static"
template_dir.mkdir(parents=True, exist_ok=True)
static_dir.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, template_folder=str(template_dir), static_folder=str(static_dir))
cfg = load_config()
app.config["SECRET_KEY"] = cfg.get("app", {}).get("secret_key", "change-this-secret")
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
app.jinja_env.auto_reload = True
app.jinja_env.cache = None

# Scheduler (singleton)
scheduler = BackgroundScheduler(daemon=True)
scheduler_started = False


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            if request.path.startswith("/api") or request.is_json:
                return jsonify({"error": "未登录"}), 401
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)

    return wrapper


@app.errorhandler(500)
def internal_error(error):
    logger.error("服务器内部错误: %s", error)
    return "服务器内部错误，请查看服务端日志。", 500


@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException):
        return e
    logger.error("未处理异常: %s", e, exc_info=True)
    return f"错误：{str(e)}", 500


def build_charts():
    """
    兼容旧脚本/测试用的图表生成函数。
    """
    try:
        cfg = load_config()
        days = int(cfg.get("app", {}).get("data_days_window", 30))
        df = load_jobs(days=days)
        if len(df) == 0:
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
        logger.error("图表构建失败: %s", e, exc_info=True)
        import pandas as pd

        return pd.DataFrame()


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/favicon.ico")
def favicon():
    return ("", 204)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username or not password:
            error = "请输入用户名和密码。"
        else:
            with Session(ENGINE) as sess:
                user = sess.query(User).filter(User.username == username).first()
                if not user or not check_password_hash(user.password_hash, password):
                    error = "用户名或密码错误。"
                elif not user.is_active:
                    error = "账号已被禁用。"
                else:
                    session["user_id"] = user.id
                    session["username"] = user.username
                    next_url = request.args.get("next") or url_for("index")
                    return redirect(next_url)
    return render_template("login.html", error=error)


@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""
        if not username or not email or not password:
            error = "请填写所有必填项。"
        elif password != confirm:
            error = "两次输入的密码不一致。"
        else:
            with Session(ENGINE) as sess:
                exists = sess.query(User).filter((User.username == username) | (User.email == email)).first()
                if exists:
                    error = "用户名或邮箱已存在。"
                else:
                    user = User(
                        username=username,
                        email=email,
                        password_hash=generate_password_hash(password),
                        is_active=True,
                    )
                    sess.add(user)
                    sess.commit()
                    session["user_id"] = user.id
                    session["username"] = user.username
                    return redirect(url_for("index"))
    return render_template("register.html", error=error)


@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.get("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/api/autocomplete", methods=["GET"])
@login_required
def autocomplete_data():
    try:
        days = int(load_config().get("app", {}).get("data_days_window", 30))
        df = load_jobs(days=days)
        cities = []
        if len(df) > 0 and "city" in df.columns:
            cities = df["city"].fillna("").dropna().unique().tolist()
            cities = [c for c in cities if c and c.strip() and c != "Unknown"]
            cities = sorted(set(cities))[:50]

        skills = []
        if len(df) > 0 and "tags" in df.columns:
            c = Counter()
            for x in df["tags"].fillna("[]"):
                try:
                    arr = json.loads(x)
                    for t in arr:
                        if isinstance(t, str) and t.strip():
                            c[t.strip().lower()] += 1
                except Exception:
                    continue
            skills = [skill for skill, _ in c.most_common(100)]

        return jsonify({"cities": cities, "skills": skills})
    except Exception as e:
        logger.error("加载自动完成数据失败: %s", e, exc_info=True)
        return jsonify({"cities": [], "skills": []}), 500


@app.route("/api/dashboard/data", methods=["GET"])
@login_required
def dashboard_data():
    try:
        days = int(load_config().get("app", {}).get("data_days_window", 30))
        df = load_jobs(days=days)
        if len(df) == 0:
            return jsonify(
                {"has_data": False, "stats": {}, "city_data": [], "trend_data": [], "tags_data": []}
            )

        total_jobs = len(df)
        unique_companies = df["company"].nunique() if "company" in df.columns else 0
        unique_cities = df["city"].nunique() if "city" in df.columns else 0

        city_series = city_top(df, 20)
        city_data = [{"city": str(city), "count": int(count)} for city, count in city_series.items()]

        trend_df = trend_by_date(df)
        trend_data = []
        if len(trend_df) > 0:
            trend_data = [
                {
                    "date": row["crawl_date"].strftime("%Y-%m-%d")
                    if hasattr(row["crawl_date"], "strftime")
                    else str(row["crawl_date"]),
                    "count": int(row["postings"]),
                }
                for _, row in trend_df.iterrows()
            ]

        tag_series = tag_top(df, 30)
        tags_data = [{"tag": str(tag), "count": int(count)} for tag, count in tag_series.items()]

        salary_stats = {}
        if "salary_avg" in df.columns:
            salary_avg = df["salary_avg"].dropna()
            if len(salary_avg) > 0:
                salary_stats = {
                    "avg": float(salary_avg.mean()),
                    "median": float(salary_avg.median()),
                    "min": float(salary_avg.min()),
                    "max": float(salary_avg.max()),
                }

        return jsonify(
            {
                "has_data": True,
                "stats": {
                    "total_jobs": total_jobs,
                    "unique_companies": unique_companies,
                    "unique_cities": unique_cities,
                    "salary_stats": salary_stats,
                },
                "city_data": city_data,
                "trend_data": trend_data,
                "tags_data": tags_data,
            }
        )
    except Exception as e:
        logger.error("加载看板数据失败: %s", e, exc_info=True)
        return jsonify(
            {
                "has_data": False,
                "error": str(e),
                "stats": {},
                "city_data": [],
                "trend_data": [],
                "tags_data": [],
            }
        ), 500


@app.route("/recommend", methods=["GET", "POST"])
@login_required
def recommend_page():
    try:
        cfg = load_config()
        days = int(cfg.get("app", {}).get("data_days_window", 30))
        topn = int(cfg.get("app", {}).get("topn", 20))
        w_sim = float(cfg.get("recommend", {}).get("weight_similarity", 0.75))
        w_sal = float(cfg.get("recommend", {}).get("weight_salary", 0.25))
        df = load_jobs(days=days)
        rows = []
        form_data = {}
        if request.method == "POST":
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
            rec = recommend(df, q, topk=topn, w_sim=w_sim, w_sal=w_sal)
            if len(rec) > 0:
                columns = ["title", "company", "city", "salary_raw", "detail_url", "score"]
                available_columns = [col for col in columns if col in rec.columns]
                rows = rec[available_columns].to_dict("records")
        return render_template("recommend.html", rows=rows, form_data=form_data)
    except Exception as e:
        logger.error("推荐页面异常: %s", e, exc_info=True)
        return "服务器内部错误", 500


@app.route("/crawl", methods=["POST"])
@login_required
def crawl_now():
    try:
        keyword = request.form.get("keyword") or "python"
        city = request.form.get("city") or ""
        platform = request.form.get("platform") or "remoteok"
        if platform not in ["remoteok", "job51", "zhilian", "wuba58"]:
            platform = "remoteok"
        if platform in ["zhilian", "wuba58"]:
            return (
                jsonify(
                    {
                        "success": False,
                        "message": f"{platform} 平台当前为占位入口，暂未接入采集能力。",
                        "error": "placeholder_platform",
                    }
                ),
                400,
            )
        result = crawl_once(keyword=keyword, city=city or None, pages=10, platform=platform)
        return jsonify(
            {
                "success": True,
                "message": f"采集完成，共 {result['count']} 条岗位。",
                "data": result,
            }
        ), 200
    except Exception as e:
        logger.error("采集失败: %s", e, exc_info=True)
        return jsonify({"success": False, "message": f"采集失败：{str(e)}", "error": str(e)}), 500


def schedule_daily_crawl(hour: int, minute: int) -> None:
    cfg = load_config()
    keyword = cfg.get("crawler", {}).get("default_keyword", "python")
    platform = cfg.get("crawler", {}).get("default_platform", "remoteok")

    def scheduled_crawl():
        try:
            result = crawl_once(keyword=keyword, city=None, pages=1, platform=platform)
            logger.info("定时采集完成：%s 条（平台=%s）", result["count"], platform)
        except Exception as e:
            logger.error("定时采集失败: %s", e, exc_info=True)

    scheduler.add_job(
        scheduled_crawl,
        "cron",
        hour=hour,
        minute=minute,
        id="daily_crawl",
        replace_existing=True,
    )


def start_scheduler():
    global scheduler_started
    if scheduler_started:
        return
    if app.debug and os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        return
    schedule_daily_crawl(9, 0)
    scheduler.start()
    scheduler_started = True


if __name__ == "__main__":
    start_scheduler()
    app.run(debug=True)
