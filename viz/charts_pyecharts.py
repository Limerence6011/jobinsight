from __future__ import annotations
from pyecharts.charts import Bar, Line, WordCloud
from pyecharts import options as opts
import pandas as pd

def bar_city(city_series: pd.Series):
    if len(city_series) == 0:
        # 返回空图表
        return (
            Bar()
            .add_xaxis(["暂无数据"])
            .add_yaxis("岗位数", [0])
            .set_global_opts(
                title_opts=opts.TitleOpts(title="城市/地区岗位热度 Top（暂无数据）"),
            )
        )
    return (
        Bar()
        .add_xaxis(list(city_series.index))
        .add_yaxis("岗位数", list(city_series.values))
        .set_global_opts(
            title_opts=opts.TitleOpts(title="城市/地区岗位热度 Top"),
            datazoom_opts=[opts.DataZoomOpts()],
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=30)),
        )
    )

def line_trend(trend_df: pd.DataFrame):
    if len(trend_df) == 0 or "crawl_date" not in trend_df.columns:
        return (
            Line()
            .add_xaxis(["暂无数据"])
            .add_yaxis("岗位数", [0])
            .set_global_opts(title_opts=opts.TitleOpts(title="岗位数量趋势（暂无数据）"))
        )
    x = trend_df["crawl_date"].dt.strftime("%Y-%m-%d").tolist()
    y = trend_df["postings"].tolist()
    return (
        Line()
        .add_xaxis(x)
        .add_yaxis("岗位数", y, is_smooth=True)
        .set_global_opts(title_opts=opts.TitleOpts(title="岗位数量趋势（按采集日期）"))
    )

def wordcloud_tags(tag_series: pd.Series):
    if len(tag_series) == 0:
        return (
            WordCloud()
            .add(series_name="技能/标签", data_pair=[("暂无数据", 1)], word_size_range=[12, 60])
            .set_global_opts(title_opts=opts.TitleOpts(title="技能/标签词云（暂无数据）"))
        )
    data = [(k, int(v)) for k, v in tag_series.items()]
    return (
        WordCloud()
        .add(series_name="技能/标签", data_pair=data, word_size_range=[12, 60])
        .set_global_opts(title_opts=opts.TitleOpts(title="技能/标签词云（Top）"))
    )
