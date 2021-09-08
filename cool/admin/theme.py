# encoding: utf-8
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

THEME_DEFAULT_PARAMS = {
    "primary": "#79aec8",  # 站点主色调
    "secondary": "#417690",  # 头部背景色及按钮背景色默认值
    "accent": "#f5dd5d",  # logo颜色
    "primary_fg": "#fff",  # 主色调背景的文字颜色
    "body_fg": "#333",  # 文字颜色
    "body_bg": "#fff",  # 页面body背景色
    "body_quiet_color": "#666",  # 标题文字颜色
    "body_loud_color": "#000",  # 关键文字颜色
    "header_color": "#ffc",  # 头部文字颜色
    "header_branding_color": None,
    "header_bg": None,  # 头部背景色
    "header_link_color": None,  # 头部链接颜色
    "breadcrumbs_fg": "#c4dce8",  # 面包屑文字颜色
    "breadcrumbs_link_fg": None,  # 面包屑链接文字颜色
    "breadcrumbs_bg": None,  # 面包屑背景色
    "module_header_bg": None,  # 模块头部背景色
    "module_header_fg": None,  # 模块头部文字颜色
    "link_fg": "#447e9b",  # 链接文字颜色
    "link_hover_color": "#036",  # 链接移入文字颜色
    "link_selected_fg": "#5b80b2",  # 过滤器中选中链接文字颜色
    "hairline_color": "#e8e8e8",  # 分割线颜色
    "border_color": "#ccc",  # 边框颜色
    "error_fg": "#ba2121",  # 错误文字颜色
    "message_success_bg": "#dfd",  # 成功消息背景色
    "message_warning_bg": "#ffc",  # 警告消息背景色
    "message_error_bg": "#ffefef",  # 错误消息背景色
    "darkened_bg": "#f8f8f8",  # 比背景稍微深点的颜色，用于表格间隔，区块区分
    "selected_bg": "#e4e4e4",  # 选中背景色，用户表格标题移入
    "selected_row": "#ffc",  # 表格行选中时背景色
    "button_fg": "#fff",  # 按钮文字颜色
    "button_bg": None,  # 按钮背景色
    "button_hover_bg": "#609ab6",  # 按钮移入时背景色
    "default_button_bg": None,  # 提交按钮背景色
    "default_button_hover_bg": "#205067",  # 提交按钮移入时背景色
    "close_button_bg": "#888",  # 关闭按钮背景色
    "close_button_hover_bg": "#747474",  # 关闭按钮移入时背景色
    "delete_button_bg": "#ba2121",  # 删除按钮背景色
    "delete_button_hover_bg": "#a41515",  # 删除按钮移入时背景色
    "object_tools_fg": None,  # 工具栏按钮文字颜色
    "object_tools_bg": None,  # 工具栏按钮背景色
    "object_tools_hover_bg": None,  # 工具栏按钮移入时背景色
    "nav_hairline_color": None,  # 导航栏分割线颜色
    "nav_body_bg": None,  # 导航栏背景色
    "nav_link_fg": None,  # 导航栏链接文字颜色
    "nav_darkened_bg": None,  # 比背景稍微深点的颜色，用于表格间隔
    "nav_header_color": None,  # 导航栏当前所在app头部文字颜色
    "nav_selected_row": None,  # 导航栏选中项目背景色
    "nav_module_header_bg": None,  # 导航栏头部背景
    "nav_module_header_fg": None,  # 导航栏头部文字颜色
}

THEME_DARK_VALUE = {
    "primary": "#264b5d",
    "primary_fg": "#eee",
    "body_fg": "#eeeeee",
    "body_bg": "#121212",
    "body_quiet_color": "#e0e0e0",
    "body_loud_color": "#ffffff",
    "breadcrumbs_link_fg": "#e0e0e0",
    "breadcrumbs_bg": None,
    "link_fg": "#81d4fa",
    "link_hover_color": "#4ac1f7",
    "link_selected_fg": "#6f94c6",
    "hairline_color": "#272727",
    "border_color": "#353535",
    "error_fg": "#e35f5f",
    "message_success_bg": "#006b1b",
    "message_warning_bg": "#583305",
    "message_error_bg": "#570808",
    "darkened_bg": "#212121",
    "selected_bg": "#1b1b1b",
    "selected_row": "#00363a",
    "close_button_bg": "#333333",
    "close_button_hover_bg": "#666666",
}

THEME_DEFAULT_VALUES = {
    "header_branding_color": "accent",
    "header_bg": "secondary",
    "header_link_color": "primary_fg",
    "breadcrumbs_link_fg": "body_bg",
    "breadcrumbs_bg": "primary",
    "button_bg": "primary",
    "module_header_bg": "primary",
    "module_header_fg": "header_link_color",
    "default_button_bg": "secondary",
    "object_tools_fg": "button_fg",
    "object_tools_bg": "close_button_bg",
    "object_tools_hover_bg": "close_button_hover_bg",
    "nav_hairline_color": "hairline_color",
    "nav_body_bg": "body_bg",
    "nav_link_fg": "link_fg",
    "nav_darkened_bg": "darkened_bg",
    "nav_header_color": "header_color",
    "nav_selected_row": "selected_row",
    "nav_module_header_bg": "module_header_bg",
    "nav_module_header_fg": "module_header_fg",
}


class ThemeStyle:

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.params = THEME_DEFAULT_PARAMS.copy()
        self.params.update(kwargs)
        for key, value in THEME_DEFAULT_VALUES.items():
            if self.params[key] is None:
                self.params[key] = self.params[value]
        err_keys = list(self.params.keys() - THEME_DEFAULT_PARAMS.keys())
        if err_keys:
            raise AttributeError("unknown theme keys : '%s'" % err_keys)

    @property
    def style(self):
        style = ":root{\n"
        for key, value in self.params.items():
            style += "  --%s: %s;\n" % (key.replace("_", "-"), value)
        style += "}\n"
        return style

    def get_dark_theme_style(self):
        kwargs = self.kwargs.copy()
        kwargs.update(THEME_DARK_VALUE)
        return ThemeStyle(**kwargs)


class RandomThemeStyle(ThemeStyle):
    def __init__(self):
        import random
        kwargs = {key: "#%06x" % random.randint(0, 0xffffff) for key in THEME_DEFAULT_PARAMS.keys()}
        super().__init__(**kwargs)


class Theme:
    def __init__(self, normal_theme_style, dark_theme_style=None):
        self.normal_theme_style = normal_theme_style
        self.dark_theme_style = dark_theme_style
        assert isinstance(self.normal_theme_style, ThemeStyle)
        if self.dark_theme_style is None:
            self.dark_theme_style = self.normal_theme_style.get_dark_theme_style()
        else:
            assert isinstance(self.dark_theme_style, ThemeStyle)

    @property
    def style(self):
        style = """
<style>
%s
@media (prefers-color-scheme: dark) {
%s
}
</style>
%s
""" % (
            self.normal_theme_style.style,
            self.dark_theme_style.style,
            format_html('<link href="{}" type="text/css" rel="stylesheet">', static("cool/admin/css/theme.css"))
        )
        return mark_safe(style)


THEME_STYLES = {
    "DEFAULT": ThemeStyle(),
    "DARK": ThemeStyle().get_dark_theme_style(),
    "RANDOM": RandomThemeStyle(),
    "BLANK": ThemeStyle(
        primary="#5FB878",  # 站点主色调
        secondary="#23262E",  # 头部背景色及按钮背景色默认值
        accent="#f5dd5d",  # logo颜色
        primary_fg="#fff",  # 主色调背景的文字颜色
        body_fg="#262626",  # 文字颜色
        body_bg="#fff",  # 页面body背景色
        body_quiet_color="#262626",  # 标题文字颜色
        body_loud_color="#000",  # 关键文字颜色
        header_color="#fff",  # 头部文字颜色
        header_bg="#23262E",  # 头部背景色
        header_link_color="#fff",  # 头部链接颜色
        breadcrumbs_fg="#fff",  # 面包屑文字颜色
        breadcrumbs_link_fg="#fff",  # 面包屑链接文字颜色
        breadcrumbs_bg="#2F4056",  # 面包屑背景色
        module_header_bg="#393D49",  # 模块头部背景色
        module_header_fg="#fff",  # 模块头部文字颜色
        link_fg="#333",  # 链接文字颜色
        link_hover_color="#262626",  # 链接移入文字颜色
        link_selected_fg="#009688",  # 过滤器中选中链接文字颜色
        hairline_color="#eee",  # 分割线颜色
        border_color="#ccc",  # 边框颜色
        error_fg="#FF5722",  # 错误文字颜色
        message_success_bg="#dfd",  # 成功消息背景色
        message_warning_bg="#ffc",  # 警告消息背景色
        message_error_bg="#ffefef",  # 错误消息背景色
        darkened_bg="#FAFAFA",  # 比背景稍微深点的颜色，用于表格间隔，区块区分
        selected_bg="#e2e2e2",  # 选中背景色，用户表格标题移入
        selected_row="#009688",  # 表格行选中时背景色
        button_fg="#fff",  # 按钮文字颜色
        button_bg="#009688",  # 按钮背景色
        button_hover_bg="#32ab9f",  # 按钮移入时背景色
        default_button_bg="#5FB878",  # 提交按钮背景色
        default_button_hover_bg="#7fc693",  # 提交按钮移入时背景色
        close_button_bg="#888",  # 关闭按钮背景色
        close_button_hover_bg="#747474",  # 关闭按钮移入时背景色
        delete_button_bg="#FF5722",  # 删除按钮背景色
        delete_button_hover_bg="#ff784e",  # 删除按钮移入时背景色
        object_tools_fg="#fff",  # 工具栏按钮文字颜色
        object_tools_bg="#888",  # 工具栏按钮背景色
        object_tools_hover_bg="#747474",  # 工具栏按钮移入时背景色
        nav_hairline_color="#282b33",  # 导航栏分割线颜色
        nav_body_bg="#282b33",  # 导航栏背景色
        nav_link_fg="#e7e7e7",  # 导航栏链接文字颜色
        nav_darkened_bg="#282b33",  # 比背景稍微深点的颜色，用于表格间隔
        nav_header_color="#fff",  # 导航栏当前所在app头部文字颜色
        nav_selected_row="#009688",  # 导航栏选中项目背景色
        nav_module_header_bg="#393D49",  # 导航栏头部背景
        nav_module_header_fg="#fff",  # 导航栏头部文字颜色
    ),
}
