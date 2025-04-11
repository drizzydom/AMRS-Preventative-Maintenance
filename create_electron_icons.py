"""
Creates placeholder icons for the Electron application
"""
import os
import base64

def create_default_icons():
    # Get the base directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    electron_dir = os.path.join(base_dir, "electron_app")
    icons_dir = os.path.join(electron_dir, "icons")
    
    # Create directories if they don't exist
    os.makedirs(icons_dir, exist_ok=True)
    
    # Path for the icons
    tray_icon_path = os.path.join(icons_dir, "tray-icon.png")
    app_icon_path = os.path.join(icons_dir, "app.ico")
    
    # Minimal 16x16 PNG for tray icon (blue square)
    tray_icon_data = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAA"
        "bwAAAG8B8aLcQwAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAAC0SURBVDiNY2CgB/j/"
        "/z8GNiFhr/9MjEwYavbvWcbIwMDAwMzMXIGu4MunDwwMA/7//XsNU+V/hpz//xn+wyz59+8fw/NndxgZwYr+"
        "c5XANcBtZWB4DCI/fnyH4eDBYxgYGlYzwAUZJOEGMDAwXP33n7Hm9+8/1TAx8cAjDx7exsTInMjEwBjz6PHj"
        "A9gMiGVgYGFA1vPs2QOGh08eMzAA8/bvP38CGRgYFmBRs4CBgYGBRUjYCzORAgCSSzZC/RW0BAAAAABJRU5ErkJggg=="
    )
    
    # Basic ICO file data (16x16, 256 colors)
    app_icon_data = base64.b64decode(
        "AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAABMLAAATCwAAAAAAAAAA"
        "AAD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///"
        "wD///8A////AP///wD///8AqqqtRJaWnKWVlZqllZWbpZWVmqWVlZulqqqsRP///wD///8A////AP///"
        "wD///8A////AP///wD///8AlpacoeTk5P/j4+P/4+Pj/+Pj4//j4+P/4+Pj/+Tk5P+WlpyhYGBgBv///"
        "wD///8A////AP///wD///8AlpacoePj4/+Hh6H/hoag/4aGoP+GhqD/hoag/4eHof/j4+P/lJSZo///"
        "/wD///8A////AP///wD///8AlpacoePj4/+GhqD/hoag/4aGoP+GhqD/hoag/4aGoP/j4+P/lJSZo///"
        "wD///8A////AP///wD///8AlpacoePj4/+GhqD/hoag/4aGoP+GhqD/hoag/4aGoP/j4+P/lJSZo///"
        "wD///8A////AP///wD///8AlpacoePj4/+GhqD/hoag/4aGoP+GhqD/hoag/4aGoP/j4+P/lJSZo///"
        "wD///8A////AP///wD///8AlpacoePj4/+GhqD/hoag/4aGoP+GhqD/hoag/4aGoP/j4+P/lJSZo///"
        "wD///8A////AP///wD///8AlpacoePj4/+GhqD/hoag/1lZff9ZWX3/hoag/4aGoP/j4+P/lJSZo///"
        "wD///8A////AP///wD///8AlpacoePj4/+GhqD/UVGA/3t7k/+QkKb/WVl9/4aGoP/j4+P/lJSZo///"
        "wD///8A////AP///wD///8AlpacoePj4/+GhqD/Vlx+/8PD0//W1t//gIGY/4aGoP/j4+P/lJSZo///"
        "wD///8A////AP///wD///8AlpacoePj4/+GhqD/Vlx//6iwr//JzNf/e3+W/4aGoP/j4+P/lJSZo///"
        "wD///8A////AP///wD///8AlpacoePj4/+GhqD/UV19/32Hmf9+h5r/VVt8/4aGoP/j4+P/lJSZo///"
        "wD///8A////AP///wD///8AlpacoePj4/+GhqD/dXWO/3+DmP9/g5j/dXWO/4aGoP/j4+P/lJSZo///"
        "wD///8A////AP///wD///8AlpacoOTk5P/j4+P/4+Pj/+Pj4//j4+P/4+Pj/+Pj4//k5OT/lJSZo///"
        "wD///8A////AP///wD///8AqqqqFZaWnKSVlZuklZWbpJWVm6SVlZuklZWbpJWVm6SVlZukrKyrFf///"
        "wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///wD///8A////AP///"
        "wD///8A8A8AAA=="
    )
    
    # Write the files
    with open(tray_icon_path, 'wb') as f:
        f.write(tray_icon_data)
    
    with open(app_icon_path, 'wb') as f:
        f.write(app_icon_data)
    
    print(f"Created tray icon: {tray_icon_path}")
    print(f"Created app icon: {app_icon_path}")

if __name__ == "__main__":
    create_default_icons()
