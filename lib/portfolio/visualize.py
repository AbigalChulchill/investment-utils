from rich.tree import Tree
from rich import print
from typing import Any
from lib.common.id_ticker_map import get_id_sym, get_id_name, get_id_name_shorter

def visualize_portfolio_tree_structure(src: dict):
    tree = Tree("", hide_root=True)

    def process_node(node: dict, rich_node: Any, pcv: float, level: int):
        if node['value'] == 0:
            return
        has_children = len(node['children']) > 0
        color_pcv = "grey62" if has_children else "cyan1"
        color_v = "wheat1"
        text_field_width = 60 - level*4
        
        if has_children:
            title = "{:<{w}}".format(node['name'],w=text_field_width+6)
        else:
            sym = get_id_sym(node['name'])
            name = get_id_name_shorter(node['name'])
            if sym == name:
                title = "{:<{w}}".format(sym,w=text_field_width+6)
            else:
                title = f"{sym:6s}" + "{:<{w}}".format(name,w=text_field_width)
        sub_node = rich_node.add(title + f"[{color_pcv}]{pcv*100:>9.1f}[/{color_pcv}]%" + f" ($[{color_v}]{node['value']:>6.0f}[/{color_v}]) ")
        if has_children:
            for ch in sorted(node['children'], key=lambda x: x['value'], reverse=True):
                process_node(ch, sub_node, ch['value']/node['value'], level + 1)
        
    process_node(src, tree, 1, 0)

    print(tree)
