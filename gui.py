import sys
import rasterio
import os
from os.path import basename
from scipy.interpolate import interp1d
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QApplication, QListWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QSlider, QAbstractItemView, QCheckBox, QFileDialog, QRadioButton
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pathplan.path_planner import plan_path
from pathplan.utils import save_path,read_init_path
from pathplan.viz import plot2d, plot3d, plot_lidar_penetration, display_surface
from pathplan.viz import plot_lidar_penetration as plot_lidar
from pathplan.evaluation import get_comparison_stats, get_individual_stats
from main import generate_path, create_test_case, load_test_case, generate_flight
import json

from matplotlib.colors import get_named_colors_mapping, to_rgb
import random

colors = list(get_named_colors_mapping().items())

print(get_named_colors_mapping().items())

class Gui(QWidget):

    def __init__(self):
        super(Gui, self).__init__()
        #TODO Set to some default params
        self.lidar_checked = False
        self.flight_checked = False
        self.flights = {}
        self.diff_checked = False
        self.default_params = 'tests/params/base.json'
        self.current_params = json.load(open(self.default_params))
        self.params = {}
        self.paths = {}
        self.start_dialogs()

        self.fig = Figure()
        self.plotter = FigureCanvas(self.fig)


        self.surface = None
        self.load_lines()
        self.surface_checked = False
        self.load_paths()
        self.init_ui()
        print(self.paths, "self.paths")
        print(self.current_paths, "self.current_paths")
        print(self.params, "self.params")

    def plot_surface_difference(self, path1, path2, ax):
        display_surface(path1, path2, ax)

    def load_paths(self):
        for path in self.tc['results']:
            self.paths[path], _ = read_init_path(self.tc['results'][path]['gen-path'])
            self.params[path] = json.load(open(self.tc['results'][path]['params']))

            if 'flight_path' in self.tc['results'][path]:
                self.flights[path] = read_init_path(test_dict['results'][path_name]['flight_path'])
            

    def update_calculations(self):
        vals = []
        for (name,path) in self.current_paths:
            vals.append(get_individual_stats(name, path))

        for i in range(0, len(self.current_paths)):
            for j in range(i+1, len(self.current_paths)):
                n1,p1 = self.current_paths[i]
                n2,p2 = self.current_paths[j]
                vals.append(get_comparison_stats(p1, p2, n1, n2))

        self.metric_printout.setText('\n'.join(vals))        
                    

    def load_lines(self):
        self.surface = json.load(open(self.tc['lines']))

    def change_selected_paths(self):
        selected_items = self.path_list.selectedItems()

        if len(selected_items) == 0:
            self.path_list.setCurrentItem(self.path_list.item(0))
            selected_items = self.path_list.selectedItems()

        self.current_paths = []

        color_idx = 1

        plot_colors = []

        for item in selected_items:
            colo = QColor(colors[color_idx][1])
            item.setForeground(colo)
            plot_colors.append(colors[color_idx][0])
            text = str(item.text())
            self.current_paths.append((text, self.paths[text]))
            color_idx += 1
      
        text = self.current_paths[0][0]
        self.current_parms = self.params[text]
        self.update_parms()
        
        self.update_calculations()
        self.reset_plots(colors[0][0], plot_colors)

    def update_parms(self):
        for (parm, val) in self.current_params.items():
            slider, label = self.slider_dict[parm]
            slider.setValue(val)
            label.setText("{0}: {1}".format(parm, val))

    def reset_parms(self, parm, vbox):
        self.slider_dict = {}
        for param,val in parm.items():
            label = QLabel(self.param_list)
            label.setText("{0}: {1}".format(param, val))
            vbox.addWidget(label)
            slider = QSlider(Qt.Horizontal)
            slider.setFocusPolicy(Qt.StrongFocus)
            slider.setTickPosition(QSlider.TicksBothSides)
            slider.setSingleStep(1)
            slider.setTickInterval(10)
            slider.setValue(val)

            slider.valueChanged.connect(lambda x,y=param,z=label:z.setText("{0}: {1}".format(y, x)))
            self.slider_dict[param] = slider, label
            vbox.addWidget(slider)

    def get_special_path(self, name):
        if self.surface == None:
            return self.load_lines()
        return self.surface
        

    def reset_plots(self, surf_color=colors[0][0], graph_colors=[]):
        if self.surface_checked:
            self.plot(('surface',self.surface), *self.current_paths, surf_color=surf_color, colors=graph_colors)
        else:
            self.plot(('surface',[]), *self.current_paths, surf_color=surf_color, colors=graph_colors)

    def set_checkboxes(self, vbox):
        self.surface_checkbox = QCheckBox("Show Surface")
        self.surface_checkbox.stateChanged.connect(lambda state: self.surface_checked_change(state))

        self.canopy_checkbox = QCheckBox("Show Canopy")
        vbox.addWidget(self.canopy_checkbox)

        vbox.addWidget(self.surface_checkbox)
        self.flight_checkbox = QCheckBox("Show Flight (if available)",)

        self.flight_checkbox.stateChanged.connect(lambda state: self.flight_checked_change("flight", state))
        vbox.addWidget(self.flight_checkbox)

        self.lidar_checkbox = QCheckBox("Lidar Penetration View")
        self.lidar_checkbox.stateChanged.connect(lambda state: self.lidar_checked_change(state))
        vbox.addWidget(self.lidar_checkbox)

        self.diff_checkbox = QCheckBox("Path Difference View")
        self.diff_checkbox.stateChanged.connect(lambda state: self.diff_checked_change(state))
        vbox.addWidget(self.diff_checkbox)



    def diff_checked_change(self, state):
        self.diff_checked = state == Qt.Checked
        self.change_selected_paths()

    def flight_checked_change(self, state):
        self.flight_checked = state == Qt.Checked
        self.change_selected_paths()

    def plot_lidar_penetration(self, path, distance, ax):
        plot_lidar(path, distance, ax=ax)

    def surface_checked_change(self, state):
        self.surface_checked = state == Qt.Checked
        self.change_selected_paths()

    def lidar_checked_change(self, state):
        self.lidar_checked = state == Qt.Checked
        self.change_selected_paths()

        

    def start_dialogs(self):
        fname = QFileDialog.getOpenFileName(self, 'Load In Test Case File', os.getcwd())
         
        print(fname)
        if fname[0]:
            self.test_case = fname[0]
            fname = fname[0]
        #This part is actualy disgusting
        #Ok its not disgusting anymore
        else:
            self.be_dem, _ = QFileDialog.getOpenFileName(self, 'Bare Earth DEM', os.getcwd())

            if not self.be_dem:
                sys.exit()
            self.canopy_dem, _ = QFileDialog.getOpenFileName(self, 'Canopy DEM', os.getcwd())
            if not self.canopy_dem:
                sys.exit()
            self.path_file, _ = QFileDialog.getOpenFileName(self, 'Initial Path', os.getcwd())
            if not self.path_file:
                sys.exit()
            fname = basename(os.path.splitext(self.path_file)[0]) + ".test"
            create_test_case(fname, self.be_dem, self.path_file, True, 'doesnt matter')

        self.init_path, self.alt_dict, self.shapes, self.tif, self.utm_projection, self.tif_projection, self.tc = load_test_case(self.test_case)

        self.raster = rasterio.open(self.tc['tif'])

        if 'initial' not in self.tc:
            self.paths['initial'] = generate_path(fname, 'test path', self.default_params)
            self.test_case = fname
            self.params['initial'] = self.default_params

        self.current_paths = [val for val in self.paths.items()]
          
          
    def plot(self, *paths, **kwargs):
        if self.flight_checked:
            for (name,_) in self.current_paths:
                if name in self.flights:
                    paths.append(name+'-flight', self.flights[name])
        if self.two_d:
            ax = self.fig.add_subplot(111) 
            ax.clear()
            plot2d(*paths, ax=ax, **kwargs)

            if self.lidar_checked:
                for (name,path) in self.current_paths:
                    be_buf = self.current_params['be_buffer']
                    print('plotting lidar')
                    self.plot_lidar_penetration(path, be_buf,  ax)
        else:
            ax = self.fig.add_subplot(111, projection='3d')
            ax.clear()
            if paths[0][0] == 'surface':
                plot3d(self.tif[0, :, :], self.raster, self.utm_projection, *paths[1:], ax=ax, **kwargs)
            else:
                kwargs['plot_surface'] = False
                plot3d(self.tif[0, :, :], self.raster, self.utm_projection, *paths, ax=ax, **kwargs)

            if self.diff_checked and len(self.current_paths) > 1:
                for i in range(0, len(self.current_paths)):
                    for j in range(i+1, len(self.current_paths)):
                        p1 = self.current_paths[i][1]
                        p2 = self.current_paths[j][1]
                        display_surface(p1, p2, ax)


        self.plotter.draw()
        

    def add_path(self):
        parms = {parm:slider.value() for (parm,(slider,_)) in self.slider_dict.items()}
        path_name = 'path-{0}'.format(len(self.paths))
        filename = 'tests/params/{0}.json'.format(path_name)
        json.dump(parms, open(filename, 'w'))
        self.paths[path_name] = generate_path(self.test_case, path_name, filename)
        self.params[path_name] = parms
        self.path_list.addItem(path_name)
        last_item = self.path_list.item(len(self.path_list)-1)
        self.path_list.setCurrentItem(last_item, True)

        self.change_selected_paths()
        

        

    def fly_path(self, path_name):
        flown_path = generate_flight(self.test_case, path_name, 5760, 'tests/flights/{0}'.format(path_name))

        self.flights[path_name] = flown_path

        

    def init_ui(self):
        grid = QGridLayout()


        self.path_list = QListWidget(self)
  
        self.path_list.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.metric_printout = QTextEdit(self)
        self.metric_printout.setReadOnly(True)


        for p in self.paths:
            self.path_list.addItem(p)

        self.path_list.itemSelectionChanged.connect(self.change_selected_paths)
        self.param_list = QWidget()
        self.parm_vbox = QVBoxLayout()

        title = QLabel(self.param_list)
        title.setText("Parameter List")
        self.parm_vbox.addWidget(title)

        self.reset_parms(self.current_params, self.parm_vbox)
 

        self.gen_button = QPushButton("New Path", self)
        self.gen_button.clicked.connect(self.add_path)
        self.parm_vbox.addWidget(self.gen_button)

        self.fly_button = QPushButton("Fly", self)
        self.fly_button.clicked.connect(lambda x: self.fly_path(self.path_list.currentItem().text()))
        self.parm_vbox.addWidget(self.fly_button)

        self.param_list.setLayout(self.parm_vbox)

        grid.addWidget(self.path_list, 1, 1)
        grid.addWidget(self.param_list, 0, 1)
        grid.addWidget(self.metric_printout, 1, 0)
        self.setLayout(grid)
 
        graph_vbox = QVBoxLayout()

        dimen_hbox = QHBoxLayout()

        rad1 = QRadioButton("2D")
        rad2 = QRadioButton("3D")

        self.two_d = True
        def lambda1():
            self.two_d = rad1.isChecked()
            self.change_selected_paths()

        def lambda2():
            self.two_d = not rad2.isChecked()
            self.change_selected_paths()

        rad1.toggled.connect(lambda1)
        rad2.toggled.connect(lambda2)

        dimen_hbox.addWidget(rad1)
        dimen_hbox.addWidget(rad2)

        rad_widg = QWidget()
        rad_widg.setLayout(dimen_hbox)

        graph_vbox.addWidget(self.plotter)
        graph_vbox.addWidget(rad_widg)

        graph_widg = QWidget()
        graph_widg.setLayout(graph_vbox)

        grid.addWidget(graph_widg, 0, 0)

        self.set_checkboxes(self.parm_vbox)
        self.change_selected_paths()

        self.show()

    def sample_plot(self):
        xs = list(range(0, 30))
        ys = list(range(2, 32))

        self.ax.clear()
        self.ax.plot(xs, ys)


if __name__ =='__main__':
    app = QApplication(sys.argv)
    gui = Gui()
    sys.exit(app.exec_())
