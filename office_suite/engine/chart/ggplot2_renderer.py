"""ggplot2 Chart Engine — R/ggplot2 图表渲染器

通过 Rscript 调用 ggplot2 渲染图表为 PNG。
支持图表类型：bar, line, pie, scatter, area, box, violin, histogram, heatmap, density, ridge

需要环境：R 已安装，ggplot2 已装（自动检测并提示安装缺失包）
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .base import BaseChartRenderer, ChartData

_RSCRIPT_CHECK = r'''
if (!requireNamespace("ggplot2", quietly = TRUE)) {
    cat("__MISSING_GGPLOT2__")
    quit(status = 1)
}
cat("__OK__")
'''

# chart_type → ggplot2 geom 映射
_R_GEOM_MAP = {
    "bar": "geom_col",
    "column": "geom_col",
    "line": "geom_line",
    "pie": "coord_polar",
    "scatter": "geom_point",
    "area": "geom_area",
    "box": "geom_boxplot",
    "violin": "geom_violin",
    "histogram": "geom_histogram",
    "density": "geom_density",
    "heatmap": "geom_tile",
}


class Ggplot2Renderer(BaseChartRenderer):
    name = "ggplot2"
    install_hint = "需要 R 环境 + ggplot2 包: install.packages('ggplot2')"

    def is_available(self) -> bool:
        try:
            result = subprocess.run(
                ["Rscript", "-e", _RSCRIPT_CHECK],
                capture_output=True, text=True, timeout=15,
            )
            return "__OK__" in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def render(
        self,
        chart_type: str,
        data: ChartData,
        extra: dict[str, Any],
        output_path: Path,
        width_px: int = 1920,
        height_px: int = 1080,
        dpi: int = 150,
    ) -> Path:
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # 将数据序列化为 JSON 供 R 读取
        data_json = self._serialize_data(chart_type, data, extra)
        r_code = self._build_r_code(chart_type, data_json, extra,
                                    width_px, height_px, dpi,
                                    str(output_path).replace("\\", "/"))

        # 写入临时 R 脚本并执行
        with tempfile.NamedTemporaryFile(mode="w", suffix=".R",
                                         delete=False, encoding="utf-8") as f:
            f.write(r_code)
            r_script_path = f.name

        try:
            result = subprocess.run(
                ["Rscript", r_script_path],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                raise RuntimeError(f"ggplot2 渲染失败:\n{result.stderr}")
        finally:
            Path(r_script_path).unlink(missing_ok=True)

        return output_path

    def _serialize_data(self, chart_type: str, data: ChartData,
                        extra: dict) -> str:
        """将 ChartData 序列化为 JSON，R 侧 jsonlite::fromJSON 读取"""
        payload: dict[str, Any] = {
            "categories": data.categories,
            "series": data.series,
            "chart_type": chart_type,
        }
        if data.raw_data is not None:
            payload["raw_data"] = data.raw_data
        return json.dumps(payload, ensure_ascii=False)

    def _build_r_code(self, chart_type: str, data_json: str,
                      extra: dict, width_px: int, height_px: int,
                      dpi: int, output_path: str) -> str:
        """构建完整的 R 脚本"""
        title = extra.get("title", "").replace("'", "\\'").replace('"', '\\"')
        colors = extra.get("colors", [
            "#1E40AF", "#3B82F6", "#60A5FA", "#93C5FD",
            "#DC2626", "#F97316", "#10B981", "#8B5CF6",
        ])
        color_vec = 'c(' + ', '.join(f'"{c}"' for c in colors) + ')'
        theme_name = extra.get("theme", "minimal")
        font_family = extra.get("font_family", "Microsoft YaHei UI").replace("'", "\\'")
        xlabel = extra.get("xlabel", extra.get("x_label", "")).replace("'", "\\'")
        ylabel = extra.get("ylabel", extra.get("y_label", "")).replace("'", "\\'")
        legend_pos = extra.get("legend_position", "bottom")

        w_in = width_px / dpi
        h_in = height_px / dpi

        return f'''
suppressPackageStartupMessages({{
    library(ggplot2)
}})

# 读取数据
data_json <- '{data_json}'
d <- jsonlite::fromJSON(data_json)

categories <- d$categories
series <- d$series

# 构建长格式数据框
df_list <- list()
for (i in seq_along(series)) {{
    s <- series[[i]]
    n <- length(s$values)
    df_list[[i]] <- data.frame(
        category = if (length(categories) >= n) categories[1:n] else as.character(1:n),
        value = as.numeric(s$values),
        series = if (!is.null(s$name)) s$name else paste0("S", i),
        stringsAsFactors = FALSE
    )
}}
df <- do.call(rbind, df_list)

# 通用主题设置
base_theme <- theme_{theme_name}() +
    theme(
        text = element_text(family = "{font_family}"),
        plot.title = element_text(size = 16, face = "bold", hjust = 0.5),
        legend.position = "{legend_pos}",
        plot.background = element_rect(fill = "transparent", color = NA),
        panel.background = element_rect(fill = "transparent", color = NA)
    )

p <- NULL

chart_type <- "{chart_type}"

if (chart_type %in% c("bar", "column")) {{
    p <- ggplot(df, aes(x = category, y = value, fill = series)) +
        geom_col(position = position_dodge(width = 0.8), width = 0.7) +
        scale_fill_manual(values = {color_vec})

}} else if (chart_type == "line") {{
    p <- ggplot(df, aes(x = category, y = value, color = series, group = series)) +
        geom_line(linewidth = 1.2) +
        geom_point(size = 3) +
        scale_color_manual(values = {color_vec})

}} else if (chart_type == "scatter") {{
    # 散点图：需要 x, y 字段
    scatter_df <- df
    if ("x" %in% names(series[[1]])) {{
        scatter_list <- list()
        for (i in seq_along(series)) {{
            s <- series[[i]]
            scatter_list[[i]] <- data.frame(
                x = as.numeric(s$x),
                y = as.numeric(if (!is.null(s$y)) s$y else s$values),
                series = if (!is.null(s$name)) s$name else paste0("S", i),
                stringsAsFactors = FALSE
            )
        }}
        scatter_df <- do.call(rbind, scatter_list)
    }}
    p <- ggplot(scatter_df, aes(x = x, y = y, color = series)) +
        geom_point(size = 3, alpha = 0.7) +
        scale_color_manual(values = {color_vec})

}} else if (chart_type %in% c("pie", "doughnut")) {{
    pie_df <- df[!duplicated(df$category), ]
    pie_df$fraction <- pie_df$value / sum(pie_df$value)
    pie_df$ymax <- cumsum(pie_df$fraction)
    pie_df$ymin <- c(0, head(pie_df$ymax, -1))
    inner_radius <- if ("{chart_type}" == "doughnut") 0.4 else 0.0
    p <- ggplot(pie_df, aes(ymax = ymax, ymin = ymin, xmax = 4, xmin = inner_radius * 4, fill = category)) +
        geom_rect() +
        coord_polar(theta = "y") +
        xlim(c(0, 4)) +
        scale_fill_manual(values = {color_vec}) +
        theme_void()

}} else if (chart_type == "area") {{
    p <- ggplot(df, aes(x = category, y = value, fill = series, group = series)) +
        geom_area(position = "identity", alpha = 0.3) +
        geom_line(aes(color = series), linewidth = 1) +
        scale_fill_manual(values = {color_vec}) +
        scale_color_manual(values = {color_vec})

}} else if (chart_type == "box") {{
    p <- ggplot(df, aes(x = series, y = value, fill = series)) +
        geom_boxplot(alpha = 0.6) +
        scale_fill_manual(values = {color_vec})

}} else if (chart_type == "violin") {{
    p <- ggplot(df, aes(x = series, y = value, fill = series)) +
        geom_violin(alpha = 0.6) +
        geom_boxplot(width = 0.1, fill = "white", alpha = 0.8) +
        scale_fill_manual(values = {color_vec})

}} else if (chart_type == "histogram") {{
    p <- ggplot(df, aes(x = value, fill = series)) +
        geom_histogram(bins = {extra.get("bins", 20)}, alpha = 0.6, position = "identity") +
        scale_fill_manual(values = {color_vec})

}} else if (chart_type == "density") {{
    p <- ggplot(df, aes(x = value, fill = series)) +
        geom_density(alpha = 0.4) +
        scale_fill_manual(values = {color_vec})

}} else if (chart_type == "heatmap") {{
    df$row_id <- as.numeric(factor(df$series))
    df$col_id <- as.numeric(factor(df$category))
    p <- ggplot(df, aes(x = category, y = series, fill = value)) +
        geom_tile(color = "white") +
        scale_fill_gradient(low = "#FFF7BC", high = "#D95F0E") +
        geom_text(aes(label = round(value, 1)), size = 3)

}} else {{
    # 默认柱状图
    p <- ggplot(df, aes(x = category, y = value, fill = series)) +
        geom_col(position = position_dodge()) +
        scale_fill_manual(values = {color_vec})
}}

# 通用标注
if (!is.null(p) && chart_type %in% c("pie", "doughnut")) {{
    p <- p + base_theme
}} else if (!is.null(p)) {{
    p <- p + base_theme +
        labs(title = "{title}", x = "{xlabel}", y = "{ylabel}")
}}

# 保存
ggsave(
    filename = "{output_path}",
    plot = p,
    width = {w_in},
    height = {h_in},
    dpi = {dpi},
    bg = "transparent"
)
'''
