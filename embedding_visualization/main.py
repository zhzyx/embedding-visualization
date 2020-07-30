from bokeh.plotting import figure, curdoc, show
from bokeh.models import HoverTool, TapTool, CrosshairTool, Circle
from bokeh.transform import factor_cmap, linear_cmap
from bokeh.palettes import Spectral6, Plasma256, inferno, cividis 
from bokeh.layouts import row, column
from bokeh.models import ColumnDataSource, HoverTool, PanTool, ResetTool,BoxZoomTool, ColorBar, CustomJS
from bokeh.models.mappers import LinearColorMapper
from bokeh.models.tools import TapTool, WheelZoomTool
from bokeh.models.widgets import Button, Slider, TextInput, RadioButtonGroup, Dropdown, Select, MultiSelect, PreText
import colorcet as cc
import os
import pandas as pd
import numpy as np
from helpers import load_csv

csv_data_dir = './embedding_visualization/data/'

def big_palette(size, palette_func): 
    if size < 256: 
        if type(palette_func) is list:
            return palette_func
        else:
            return palette_func(size) 
        
    if type(palette_func) is list:
        p = palette_func
    else:
        p = palette_func(256) 
    out = [] 
    for i in range(size):
        idx = int(i * 256.0 / size) 
        out.append(p[idx])
    return out  

def get_color_mapper(field_name):
    cls_list = data_df[field_name].unique()
    if np.issubdtype(data_df[field_name].dtype, np.number):
        is_numeric = True
        cmap = linear_cmap(field_name, palette=cc.rainbow, low=min(cls_list), high=max(cls_list), nan_color=(0, 0, 0, 0))
    else:
        is_numeric = False
        cmap = factor_cmap(field_name, palette=big_palette(len(cls_list), cc.glasbey), factors=cls_list, nan_color=(0, 0, 0, 0))
    return cmap, cls_list, is_numeric

def generate_tooltip_html():
    base_code = """
    <style>
        .bk-tooltip>div:not(:first-child) {{display:none;}}
    </style>
    <div>
        {}
        <div>
            {}
        </div>
        <div>
            <span style="font-size: 10px; color: #696;">($x, $y)</span>
        </div>
    </div>
    """
    image_code = ""
    if 'image_path' in data_df:
        image_code = """
        <div>
            <img
                src="/embedding_visualization/static/@image_path" height="100" alt="@image_path" width="100"
                style="margin: 0px 0px 15px 0px;"
                border="2"
            ></img>
        </div>
        """
    label_code = ""
    for feature in features_list:
        if np.issubdtype(data_df[feature].dtype, np.float):
            label_code += f"""<li style="font-size: 12px; font-weight: bold; color: #966;">{feature}: @{feature}</li>\n"""
        else:
            label_code += f"""<li style="font-size: 12px; font-weight: bold; color: #966;">{feature}: @{feature}</li>\n"""
    return base_code.format(image_code, label_code)

def update_file_list():
    csv_list = os.listdir(csv_data_dir)
    menu = [('refresh list', 'refresh_list'), None]
    for i, filename in enumerate(csv_list):
        if filename[-4:] == '.csv':
            menu.append((filename, filename))
    file_select_dropdown.menu=menu

def load_data(file_name):
    global data_df 
    global features_list
    global source
    try:
        read_data_df = load_csv(os.path.join(csv_data_dir, file_name))
    except Exception as e:
        print(e)
    data_df = read_data_df
    features_list = [i for i in list(data_df.columns) if i not in ['tsne_x', 'tsne_y', 'image_path']]
    # source = ColumnDataSource(data_df)
    cr.data_source.data = data_df
    toggle_class_select.options = features_list
    toggle_class_select.value = features_list[0]
    update_toggle_class('value', None, features_list[0])
    color_class_select.options = features_list
    color_class_select.value = features_list[0]
    update_color_class('value', None, features_list[0])
    update_class_selection('value', None, [])
    hover_tip_tool.tooltips = generate_tooltip_html()

data_df = load_csv('./embedding_visualization/data/show.csv')
features_list = [i for i in list(data_df.columns) if i not in ['tsne_x', 'tsne_y']]
source = ColumnDataSource(data_df)

cls_color_mapper, color_cls_list, _ = get_color_mapper(features_list[0])
p = figure(plot_width=800, plot_height=800, match_aspect=True, tools=['pan', 'box_zoom', 'reset'], title='', 
           sizing_mode='scale_height', output_backend="webgl")
cr = p.circle(x='tsne_x', y='tsne_y', color=cls_color_mapper, source=source)
cr.selection_glyph = Circle(fill_color=cls_color_mapper, line_color=cls_color_mapper)
cr.nonselection_glyph = Circle(fill_color=cls_color_mapper, line_color=cls_color_mapper, fill_alpha=0.05, line_alpha=0.05)
color_bar = ColorBar(color_mapper=LinearColorMapper(palette="Viridis256", low=1, high=10), label_standoff=12, border_line_color=None, location=(0,0))
p.add_layout(color_bar, 'right')
color_bar.visible = False
if type(cls_color_mapper['transform']) is LinearColorMapper:
    color_bar.color_mapper = cls_color_mapper['transform']
    # p.add_layout(color_bar, 'right')
    color_bar.visible = True
# Define widgets
hover_tip_tool = HoverTool(tooltips=generate_tooltip_html(), show_arrow=False, renderers=[cr])
wheel_zoom_tool = WheelZoomTool()
file_select_dropdown = Dropdown(label="Data file", button_type="warning", height_policy='min', menu=[('refresh list', 'refresh_list'), None])
update_file_list()
color_class_select = Select(title="Colored by:", value=features_list[0], options=features_list[:], sizing_mode="stretch_width")
toggle_class_select = Select(title="Selected by:", value=features_list[0], options=features_list[:], sizing_mode="stretch_width")
class_toggle_multi_select = MultiSelect(title='toggle classes:') # , options=list(data_df[features_list[0]].unique()))
# Define widgets callbacks
def update_color_class(attr, old, new):
    print(f"{attr} changed from {old} to {new}")
    cls_color_mapper, cls_list, _ = get_color_mapper(new)
    if type(cls_color_mapper['transform']) is LinearColorMapper:
        color_bar.color_mapper.palette = cls_color_mapper['transform'].palette
        color_bar.color_mapper = cls_color_mapper['transform']
        color_bar.visible = True
    else:
        color_bar.visible = False
    print(f"cm field: {cls_color_mapper['field']}")
    cr.nonselection_glyph.fill_color = cls_color_mapper
    cr.nonselection_glyph.line_color = cls_color_mapper
    cr.selection_glyph.fill_color = cls_color_mapper
    cr.selection_glyph.line_color = cls_color_mapper
    cr.glyph.fill_color = cls_color_mapper
    cr.glyph.line_color = cls_color_mapper
    # cr.hover_glyph.fill_color = cls_color_mapper
    # cr.hover_glyph.line_color = cls_color_mapper

def update_toggle_class(attr, old, new):
    options = list(data_df[new].unique())
    options.sort()
    class_toggle_multi_select.options = list(map(str, options))

def update_class_selection(attr, old, new):
    print(f"{attr} changed from {old} to {new}")
    idx_list = []
    if np.issubdtype(data_df[toggle_class_select.value].dtype, np.number):
        new = list(map(float, new))
    for c in new:
        idx_list.extend(data_df[data_df[toggle_class_select.value] == c].index.tolist())
    source.selected.indices = idx_list

def file_select_handler(event):
    print(type(event.item))
    if event.item == 'refresh_list':
        update_file_list()
    else:
        load_data(event.item)
    
tooltip_fix_callback = CustomJS(code="""
    var tooltips = document.getElementsByClassName("bk-tooltip");
    for (var i = 0, len = tooltips.length; i < len; i ++) {
        tooltips[i].style.top = ""; // unset what bokeh.js sets
        tooltips[i].style.right = "";
        tooltips[i].style.bottom = "";
        tooltips[i].style.left = "";
        tooltips[i].style.bottom = "0px";
        tooltips[i].style.right = "-150px";
    }
    """)

# bind widget callbacks
color_class_select.on_change('value', update_color_class)
toggle_class_select.on_change('value', update_toggle_class)
class_toggle_multi_select.on_change('value', update_class_selection)
file_select_dropdown.on_click(file_select_handler)
hover_tip_tool.callback = tooltip_fix_callback

update_toggle_class('value', '', features_list[0])

control_panel = column([file_select_dropdown, color_class_select, toggle_class_select, class_toggle_multi_select], sizing_mode="stretch_height", width=200)
p.add_tools(wheel_zoom_tool)
p.add_tools(hover_tip_tool)
p.toolbar.active_scroll = wheel_zoom_tool
curdoc().add_root(row(control_panel, p, sizing_mode='stretch_both'))
'''
filelist_refresh_button = Button(label="Refresh data list", button_type="success")
menu = [("1.csv", "item_1"), ("2.csv", "item_2")]
data_dropdown = Dropdown(label="Data file", button_type="warning", menu=menu)
color_select_text = PreText(text='Color mapped by: ')
color_select_rbButton = RadioButtonGroup(labels=["classes", "linear"], active=0)
col_select = Select(title="Colored by:", value=features_list[0], options=features_list[:])
highlight_select = Select(title="Highlighted by:", value=features_list[0], options=features_list[:])
'''
