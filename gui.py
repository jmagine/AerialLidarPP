import sys
import os
from os.path import basename
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QGridLayout, QPushButton, QApplication, QListWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QPushButton, QSlider, QAbstractItemView, QCheckBox, QFileDialog
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from pathplan.path_planner import plan_path
from pathplan.viz import plot2d
from main import generate_path, create_test_case, load_test_case
import json

#class TestCaseLoader(QWidget):
#
#    def __init__(self):
#        super(TestCaseLoader, self).__init__()


class Gui(QWidget):

    def __init__(self):
        super(Gui, self).__init__()
        #Of the form {'path_name': {'param':val}}

        #TODO Set to some default params
        self.default_params = 'tests/params/base.json'
        self.current_params = json.load(open(self.default_params))
        self.params = {}
        self.paths = {}
        self.start_dialogs()

        self.fig = Figure()
        self.plotter = FigureCanvas(self.fig)


        self.init_ui()
        print(self.paths, "self.paths")
        print(self.current_paths, "self.current_paths")
        print(self.params, "self.params")

    def load_lines(self):
        _,_,_,_,_, self.tc = load_test_case(self.test_case)
        return json.load(open(self.tc['lines']))

    def change_selected_paths(self):
        selected_items = self.path_list.selectedItems()
        self.current_paths = []
        for item in selected_items:
            text = str(item.text())
            self.current_paths.append((text, self.paths[text]))
      
        first = selected_items[0]
        text = str(first.text())
        self.current_parms = self.params[text]
        self.update_parms()
        
        self.reset_plots()

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
        return self.load_lines()
        

    def reset_plots(self):
        self.plot(*self.current_paths)

    def set_checkboxes(self, vbox, imax_3d=False):
        if not imax_3d:
            self.surface_checkbox = QCheckBox("Show Surface")
            self.surface_checkbox.stateChanged.connect(lambda state: self.special_path_check("surface", state))
            vbox.addWidget(self.surface_checkbox)
            self.flight_checkbox = QCheckBox("Show Flight (if available)",)
            self.flight_checkbox.stateChanged.connect(lambda state: self.special_path_check("flight", state))
            vbox.addWidget(self.flight_checkbox)
            self.lidar_checkbox = QCheckBox("Lidar Penetration View")
            vbox.addWidget(self.lidar_checkbox)
            self.canopy_checkbox = QCheckBox("Show Canopy")
            vbox.addWidget(self.canopy_checkbox)
        else:
            pass


    def plot_lidar_penetration(self, path, surface, lidar):
        pass

    def special_path_check(self, name, state):
        if state != Qt.Checked:
            self.current_paths = [path for path in self.current_paths if path[0] != name]
        else:
            self.current_paths.insert(0, ((name, self.get_special_path(name))))
            

        print(([x[0] for x in self.current_paths], 'paths'))
        self.reset_plots()

        

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

        _,_,_,_,_, self.tc = load_test_case(self.test_case)

        if 'initial' not in self.tc:
            self.paths['initial'] = generate_path(fname, 'test path', self.default_params)
            self.test_case = fname
            self.params['initial'] = self.default_params

        self.current_paths = [val for val in self.paths.items()]
          
          

    def plot(self, *paths):
        ax = self.fig.add_subplot(111)
        ax.clear()
        plot2d(*paths, ax=ax)

        self.plotter.draw()
        

    def add_path(self):
        parms = {parm:slider.value() for (parm,(slider,_)) in self.slider_dict.items()}
        path_name = 'path-{0}'.format(len(self.paths))
        filename = 'tests/params/{0}.json'.format(path_name)
        json.dump(parms, open(filename, 'w'))
        self.paths[path_name] = generate_path(self.test_case, 'test path', filename)
        self.params[path_name] = parms
        self.path_list.addItem(path_name)
       

        

    def fly_path(self):
        pass

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
 
        self.set_checkboxes(self.parm_vbox)

        self.gen_button = QPushButton("New Path", self)
        self.gen_button.clicked.connect(self.add_path)
        self.parm_vbox.addWidget(self.gen_button)

        self.fly_button = QPushButton("Fly", self)
        self.fly_button.clicked.connect(self.fly_path)
        self.parm_vbox.addWidget(self.fly_button)

        self.param_list.setLayout(self.parm_vbox)

        grid.addWidget(self.path_list, 1, 1)
        grid.addWidget(self.param_list, 0, 1)
        grid.addWidget(self.metric_printout, 1, 0)
        self.setLayout(grid)
 
        grid.addWidget(self.plotter, 0, 0)

        self.reset_plots()

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
