"""
 -----------------------------------------------------------------------------------------------------------
 Package:    AequilibraE

 Name:       Main interface for creating stacked bandwidths for link layers
 Purpose:    Load GUI and user interface for the bandwidth creation

 Original Author:  Pedro Camargo (c@margo.co)
 Contributors:
 Last edited by: Pedro Camargo

 Website:    www.AequilibraE.com
 Repository:  https://github.com/AequilibraE/AequilibraE

 Created:    2016-10-24
 Updated:    2016-12-21
 Copyright:   (c) AequilibraE authors
 Licence:     See LICENSE.TXT
 -----------------------------------------------------------------------------------------------------------
 """

import qgis
from functools import partial
from qgis.core import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.gui import QgsMapLayerProxyModel

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"..")))

from global_parameters import *
from random import randint

from forms import Ui_bandwidths
from auxiliary_functions import *
from set_color_ramps_dialog import LoadColorRampSelector
from color_ramps import AequilibraERamps

class CreateBandwidthsDialog(QDialog, Ui_bandwidths):
    def __init__(self, iface):
        QDialog.__init__(self)
        self.iface = iface
        self.setupUi(self)
        
        self.tot_bands = 0
        self.band_size = 10.0
        self.space_size = 0.01
        self.layer = None
        self.ramps = None
        self.drive_side = get_parameter_chain(['system', 'driving side'])

        # layers and fields        # For adding skims
        self.mMapLayerComboBox.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.mMapLayerComboBox.layerChanged.connect(self.add_fields_to_cboxes)

        self.ab_FieldComboBox.currentIndexChanged.connect(partial(self.choose_a_field, 'AB'))
        self.ba_FieldComboBox.currentIndexChanged.connect(partial(self.choose_a_field, 'BA'))

        # space slider
        self.slider_spacer.setMinimum(1)
        self.slider_spacer.setMaximum(30)
        self.slider_spacer.setValue(1)
        self.slider_spacer.setTickPosition(QSlider.TicksBelow)
        self.slider_spacer.setTickInterval(5)
        self.slider_spacer.valueChanged.connect(self.spacevaluechange)

        # band slider
        self.slider_band_size.setMinimum(5)
        self.slider_band_size.setMaximum(150)
        self.slider_band_size.setValue(50)
        self.slider_band_size.setTickPosition(QSlider.TicksBelow)
        self.slider_band_size.setTickInterval(5)
        self.slider_band_size.valueChanged.connect(self.sizevaluechange)

        #List of bands
        self.bands_list.setColumnWidth(0, 210)
        self.bands_list.setColumnWidth(1, 210)
        self.bands_list.setColumnWidth(2, 110)
        self.bands_list.setColumnWidth(3, 110)

        # loading ramps
        self.but_load_ramp.setVisible(False)
        self.txt_ramp.setVisible(False)

        self.but_add_band.clicked.connect(self.add_to_bands_list)
        self.bands_list.setEditTriggers(QTableWidget.NoEditTriggers)

        # self.bands_list.doubleClicked.connect(self.slot_double_clicked)

        self.rdo_color.toggled.connect(self.color_origins)
        self.rdo_ramp.toggled.connect(self.color_origins)
        self.but_run.clicked.connect(self.add_bands_to_map)
        self.but_run.setEnabled(False)

        self.but_load_ramp.clicked.connect(self.load_ramp_action)
        self.add_fields_to_cboxes()
        self.random_rgb()
        self.sizevaluechange()
        self.spacevaluechange()
        self.set_initial_value_if_available()
        self.but_load_ramp.setEnabled(False)

    def color_origins(self):
        self.mColorButton.setVisible(self.rdo_color.isChecked())
        self.but_load_ramp.setVisible(self.rdo_ramp.isChecked())
        self.txt_ramp.setVisible(self.rdo_ramp.isChecked())
        self.but_load_ramp.setEnabled(self.rdo_ramp.isChecked())

    def choose_a_field(self, modified):
        i, j = 'AB', 'BA'

        if modified == i:
            text = self.ab_FieldComboBox.currentText()
            if i in text:
                text = text.replace(i, j)
                index = self.ba_FieldComboBox.findText(text, Qt.MatchFixedString)
                if index >= 0:
                    self.ba_FieldComboBox.setCurrentIndex(index)

        if modified == j:
            text = self.ba_FieldComboBox.currentText()
            if j in text:
                text = text.replace(j, i)
                index = self.ab_FieldComboBox.findText(text, Qt.MatchFixedString)
                if index >= 0:
                    self.ab_FieldComboBox.setCurrentIndex(index)

    def set_initial_value_if_available(self):
        all_items = [self.ab_FieldComboBox.itemText(i) for i in range(self.ab_FieldComboBox.count())]

        for i in all_items:
            if 'AB' in i:
                index = self.ab_FieldComboBox.findText(i, Qt.MatchFixedString)
                if index >= 0:
                    self.ab_FieldComboBox.setCurrentIndex(index)
                break

    def spacevaluechange(self):
        self.space_size = self.slider_spacer.value() / 100.0
        self.lbl_space.setText("{:3,.2f}".format(self.space_size))

    def sizevaluechange(self):
        self.band_size = self.slider_band_size.value() / 5.0
        self.lbl_width.setText("{:3,.2f}".format(self.band_size))

    # # Method for removing a line from the table with a double click
    # def slot_double_clicked(self, mi):
    #     row = mi.row()
    #     if row > -1:
    #         self.bands_list.removeRow(row)
    #         self.tot_bands -= 1

    def add_fields_to_cboxes(self):
        self.layer = get_vector_layer_by_name(self.mMapLayerComboBox.currentText())

        if self.layer is not None:
            self.but_load_ramp.setEnabled(True)
        else:
            self.but_load_ramp.setEnabled(False)
        self.ab_FieldComboBox.setLayer(self.layer)
        self.ba_FieldComboBox.setLayer(self.layer)

    def add_to_bands_list(self):
        if self.ab_FieldComboBox.currentIndex() >= 0 and self.ba_FieldComboBox.currentIndex() >= 0:
            ab_band = self.layer.fieldNameIndex(self.ab_FieldComboBox.currentText())
            ba_band = self.layer.fieldNameIndex(self.ba_FieldComboBox.currentText())

            self.bands_list.setRowCount(self.tot_bands + 1)

            # Field names
            self.bands_list.setItem(self.tot_bands, 0, QTableWidgetItem(self.ab_FieldComboBox.currentText()))
            self.bands_list.setItem(self.tot_bands, 1, QTableWidgetItem(self.ba_FieldComboBox.currentText()))

            # color
            if self.ramps is None:
                self.bands_list.setItem(self.tot_bands, 2, QTableWidgetItem(''))
                self.bands_list.item(self.tot_bands, 2).setBackground(self.mColorButton.color())
            else:
                self.bands_list.setItem(self.tot_bands, 2, QTableWidgetItem(str(self.ramps)))
                self.ramps = None
                self.rdo_color.setChecked(True)

            # Up-Down buttons

            button_up = QToolButton()
            button_up.setArrowType(Qt.UpArrow)
            button_up.clicked.connect(self.click_button_inside_the_list)

            button_down = QToolButton()
            button_down.setArrowType(Qt.DownArrow)
            button_down.clicked.connect(self.click_button_inside_the_list)

            del_button = QPushButton('X')
            del_button.clicked.connect(self.click_button_inside_the_list)

            layout = QHBoxLayout()
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
            layout.addWidget(button_down)
            layout.addWidget(button_up)
            layout.addWidget(del_button)

            cellWidget = QWidget()
            cellWidget.setLayout(layout)
            self.bands_list.setCellWidget(self.tot_bands, 3, cellWidget)

            # incrementing and moving on
            self.tot_bands += 1
            self.but_run.setEnabled(True)
            self.random_rgb()

    def click_button_inside_the_list(self):
        button = self.sender()
        parent = button.parent()

        for i in range(self.tot_bands):
            if self.bands_list.cellWidget(i,3) is parent:
                row = i
                break

        column = 2
        for i, q in enumerate(button.parentWidget().findChildren(QToolButton)):
            if q is button:
                column = i


        # if we clicked the "remove button"
        if column == 0 and row < self.tot_bands -1:
            low_cl = self.bands_list.item(row + 1, 2).backgroundColor()
            low_ab = self.bands_list.item(row + 1, 0).text()
            low_ba = self.bands_list.item(row + 1, 1).text()

            top_cl = self.bands_list.item(row, 2).backgroundColor()
            top_ab = self.bands_list.item(row, 0).text()
            top_ba = self.bands_list.item(row, 1).text()


            self.bands_list.setItem(row, 0, QTableWidgetItem(low_ab))
            self.bands_list.setItem(row, 1, QTableWidgetItem(low_ba))
            self.bands_list.item(row, 2).setBackground(low_cl)

            self.bands_list.setItem(row + 1, 0, QTableWidgetItem(top_ab))
            self.bands_list.setItem(row + 1, 1, QTableWidgetItem(top_ba))
            self.bands_list.item(row + 1, 2).setBackground(top_cl)

        elif column == 1 and row > 0:
            low_cl = self.bands_list.item(row, 2).backgroundColor()
            low_ab = self.bands_list.item(row, 0).text()
            low_ba = self.bands_list.item(row, 1).text()

            top_cl = self.bands_list.item(row - 1, 2).backgroundColor()
            top_ab = self.bands_list.item(row - 1, 0).text()
            top_ba = self.bands_list.item(row - 1, 1).text()

            self.bands_list.setItem(row, 0, QTableWidgetItem(top_ab))
            self.bands_list.setItem(row, 1, QTableWidgetItem(top_ba))
            self.bands_list.item(row, 2).setBackground(top_cl)

            self.bands_list.setItem(row -1, 0, QTableWidgetItem(low_ab))
            self.bands_list.setItem(row -1, 1, QTableWidgetItem(low_ba))
            self.bands_list.item(row - 1, 2).setBackground(low_cl)

        elif column == 2:
            self.bands_list.removeRow(row)
            self.tot_bands -= 1

            if self.tot_bands == 0:
                self.but_run.setEnabled(False)

    def random_rgb(self):
        rgb = []
        for i in range(3):
            rgb.append(randint(0, 255))
        a = QColor()
        a.setRgb(rgb[0], rgb[1], rgb[2])
        self.mColorButton.setColor(a)

    def load_ramp_action(self):
        self.ramps = None
        dlg2 = LoadColorRampSelector(self.iface, self.layer)
        dlg2.show()
        dlg2.exec_()
        if dlg2.results is not None:
            self.ramps = dlg2.results
            self.txt_ramp.setText(str(self.ramps))

    def add_bands_to_map(self):
        self.but_run.setEnabled(False)
        self.band_size = str(self.band_size)
        self.space_size = str(self.space_size)

        # define the side of the plotting based on the side of the road the system has defined
        ab = -1
        if self.drive_side == 'right':
            ab = 1
        ba = - ab

        bands_ab = []
        bands_ba = []
        # go through all the fields that will be used to find the maximum value. This will be used
        # to limit the size of bandwidth for all layers of bands
        values = []
        for i in range(self.tot_bands):
            for j in range(2):
                field = self.bands_list.item(i, j).text()
                idx = self.layer.fieldNameIndex(field)
                values.append(self.layer.maximumValue(idx))

                # we also build a list of bands to construct
                # The function "(2 * j -1) * ba"  maps the index j {1,2} and the direction to the side of the
                # link the band needs to be. Try it out. it works!!
                #bands.append((field, (2 * j -1) * ba, self.bands_list.item(i, 2).backgroundColor()))
            if len(self.bands_list.item(i, 2).text()) == 0:
                cl = self.bands_list.item(i, 2).backgroundColor()
            else:
                cl = eval(self.bands_list.item(i, 2).text())
            bands_ab.append((self.bands_list.item(i, 0).text(), ab, cl, 'ab'))
            bands_ba.append((self.bands_list.item(i, 1).text(), ba, cl, 'ba'))
        sides = [bands_ab, bands_ba]
        max_value = max(values)

        for s in sides:
            acc_offset = '0'
            for field, side, clr, direc in s:
                symbol_layer = QgsSimpleLineSymbolLayerV2.create({})
                props = symbol_layer.properties()
                width = '(coalesce(scale_linear("' + field + '", 0, ' + str(max_value) + ', 0, ' + self.band_size + '), 0))'
                props['width_dd_expression'] = width

                props['offset_dd_expression'] = acc_offset + '+' + str(side) + ' * (coalesce(scale_linear("' + field + \
                                                '", 0, ' + str(max_value) + ', 0, ' + self.band_size + '), 0)/2 + ' + \
                                                self.space_size + ')'
                if isinstance(clr, dict):
                    if direc == 'ab':
                        props['color_dd_expression'] = "ramp_color(\'" + clr[
                            'color ab'] + "\',scale_linear(" + '"' + clr['ramp ab'] + '", ' + str(clr[
                                                                'min ab']) + ', ' + str(clr['max ab']) + ', 0, 1))'
                    else:
                        props['color_dd_expression'] = "ramp_color(\'" + clr[
                            'color ba'] + "\',scale_linear(" + '"' + clr['ramp ba'] + '", ' + str(clr[
                                                                'min ba']) + ', ' + str(clr['max ba']) + ', 0, 1))'
                else:
                    props['line_color'] = str(clr.getRgb()[0]) + ',' + str(clr.getRgb()[1]) + ',' + str(clr.getRgb()[2]) + ',' \
                                          + str(clr.getRgb()[3])

                symbol_layer = QgsSimpleLineSymbolLayerV2.create(props)
                self.layer.rendererV2().symbol().appendSymbolLayer(symbol_layer)

                acc_offset = acc_offset + ' + ' + str(side) + '*(' + width + '+' + self.space_size + ')'

        self.layer.triggerRepaint()
        self.exit_procedure()

    def exit_procedure(self):
        self.close()


if __name__ == '__main__':
    main()