import matplotlib.pyplot as plt
from matplotlib.cm import get_cmap
import numpy as np
import pathlib
import colorsys
import hashlib

def get_color(key: str, level: int, emphasis: bool, is_borrow: bool):
    if key == "fiat":
        if is_borrow:
            return colorsys.hsv_to_rgb(0, 0.8, min(1, 0.2 + level*0.25) )
        else:
            return colorsys.hsv_to_rgb(0, 0, min(1, 0.2 + level*0.25) )        
    else:
        return get_cmap("rainbow")((int(hashlib.md5(key.encode()).hexdigest(),base=16)%255) / 255.0)



class PortfolioStructureDonutChart:
    def export(self, src: dict):

        fig, ax = plt.subplots(
            figsize=(15, 15),
            subplot_kw=dict(projection="polar")
            )

        norm_factor = 1 / src['value']
        fiat_scale = 0.25
        size = 0.3


        def get_trans_value(x: float) -> float:
            return x * norm_factor * 2 * np.pi

        def get_label(node: dict, level: int) -> str:
            sep1 = "\n" if level < 2 else " "
            sep2 = "\n" if level < 2 else " "
            return f"{node['name']}{sep1}{node['value']*norm_factor*100:.1f}%{sep2}($ {node['value']:.0f})"


        def process_branch_recursive(node: dict, xoffset: float, level: int, root_category: str):

            is_leaf = len(node['children']) == 0

            if not is_leaf:
                offset = xoffset
                for x in node['children']:
                    process_branch_recursive(x, offset, level + 1, root_category if root_category else x['name'])
                    ofset_add = get_trans_value(x['value'])
                    if root_category == "fiat":
                        ofset_add *= fiat_scale
                    ofset_add = abs(ofset_add)
                    offset += ofset_add

            if node['name'] != 'all':
                value = get_trans_value(node['value'])
                if value != 0:
                    width = abs(value)
                    if root_category == "fiat" and is_leaf:
                        width *= fiat_scale
                    bot = size*level
                    b = ax.bar(
                        x=xoffset,
                        color=get_color(root_category, level, is_leaf, value < 0),
                        width=width, bottom=bot, height=size,
                        edgecolor='w', linewidth=0.5, align="edge")
                    rot = np.rad2deg(xoffset+width*0.5) if level > 1 else 0
                    if rot > 270:
                        rot -= 360
                    elif rot > 90:
                        rot -= 180
                    ax.bar_label(b, labels=[get_label(node, level)], label_type='center', fontsize=12/level,rotation=rot)



        process_branch_recursive(src, 0, 0, "")

        #ax.set(title="Portfolio Structure")
        ax.set_axis_off()
        fig.tight_layout()


        pathlib.Path("reports").mkdir(parents=True, exist_ok=True)
        fig_file = "reports/portfolio_structure.svg"
        plt.savefig(fig_file)
        print(f"Portfolio structure chart exported as {fig_file}")
        #plt.show()
