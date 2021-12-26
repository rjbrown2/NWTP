import math
import signal
import sys

from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QDoubleValidator, QStandardItemModel, QStandardItem

import constants
import recipes

#  Global variables

class Ui(QtWidgets.QWidget):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('../config/NW_TP3.ui', self)
        self.setWindowTitle("New World Trading Post")

        #
        # Initialize components
        #
        self.buyCombo = self.findChild(QtWidgets.QComboBox, "buy_comboBox")
        self.buyCombo.currentTextChanged.connect(self.buy_combo_selected)
        self.sellCombo = self.findChild(QtWidgets.QComboBox, "sell_comboBox")
        self.sellCombo.currentTextChanged.connect(self.sell_combo_selected)
        self.buyQuantity = self.findChild(QtWidgets.QLineEdit, "buyQuantity")
        self.buyQuantity.setReadOnly(True)
        self.sellQuantity = self.findChild(QtWidgets.QLineEdit, "sellQuantity")
        self.sellQuantity.setReadOnly(True)
        self.buyIndividual = self.findChild(QtWidgets.QLineEdit, "buyIndividual")
        self.buyIndividual.setReadOnly(True)
        self.sellIndividual = self.findChild(QtWidgets.QLineEdit, "sellIndividual")
        self.sellIndividual.setReadOnly(True)
        self.buyFlip = self.findChild(QtWidgets.QLineEdit, "buyFlip")
        self.buyFlip.setReadOnly(True)
        self.sellFlip = self.findChild(QtWidgets.QLineEdit, "sellFlip")
        self.sellFlip.setReadOnly(True)
        self.capital = self.findChild(QtWidgets.QLineEdit, "Capital")
        self.onlyDouble = QDoubleValidator(0.0, 500000.00, 2)
        self.ingr_cost  = 0.0
        self.can_make = 0
        self.money = 0

        # Validate capital input (min, max, decimal) Max not working as intended
        self.capital.setValidator(self.onlyDouble)
        self.debug = self.findChild(QtWidgets.QTextEdit, "debug")
        self.debug_tree = self.findChild(QtWidgets.QTreeView, "debugTreeView")
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["Recipe", "Qty", "Cost", "Total Qty", "Total Cost"])
        self.debug_tree.header().setDefaultSectionSize(180)
        self.debug_tree.setModel(self.model)
        self.debug_tree.setColumnWidth(0, 150)
        self.debug_tree.setColumnWidth(1, 50)
        self.debug_tree.setColumnWidth(2, 50)
        #
        # End component initialization
        #

        self.show()

    def sell_combo_selected(self):
        can_make,  sell_individual, sell_flip = 0.0, 0.0, 0.0

        item = self.sellCombo.currentText()
        trans_item = lookup_dump_data(item)
        print("LOOKUP: " + item)
        print("FOUND: " + trans_item)
        output = recipes.print_results(str(trans_item))

        self.process_output(output)  # Fill QTreeView
        self.debug.setText(str(output))  # Fill RichTextBox
        # TODO:  Verify formulas for sell boxes
        capital = float(self.capital.text())
        self.money = capital
        can_make = math.floor(capital / self.ingr_cost)  # Formulate and set sell quantity ( qty can be made )
        self.sellQuantity.setText(str(can_make))
        p = lookup_prices(item)

        sell_individual = can_make * float(p[1])  # Formulate and set sell individual
        self.sellIndividual.setText(str(sell_individual))

        sell_flip = sell_individual - capital  # Formulate and set sell flip
        self.sellFlip.setText(str(sell_flip))

    def process_output(self, data_in):
        self.model.setRowCount(0)
        self.ingr_cost = 0
        recipe_split = data_in.split("\n")
        blank_list = []
        #  Iterate recipes within string
        for r in recipe_split:
            
            parent = QStandardItem(r.split(":")[0])  # Split recipe name from ingredients
            blank_list.append(parent)
            parent.setEditable(False)
            ingrs = r.split(":")[1]  # Split ingredients from recipe name
            ingrs = ingrs.rstrip(',')
            print("OUTER: " + r.split(":")[0])
            # Iterate ingredients in recipe and split ingr from qty
            for i in ingrs.split(","):
                t = i.split("-")
                # For loop causes index out of range when using t[1] outside of try except, unsure why
                try:
                    print("Inner: " + t[1])
                    ingr = QStandardItem(t[1])
                    qty = QStandardItem(t[0])
                    ingr.setEditable(False)
                    qty.setEditable(False)
                    temp_convert = None
                    temp_convert = recipes.recipe_lookup_dump_data(t[1])
                    print("TEMP CONVERT: " + str(temp_convert))
                    if (temp_convert is not None):
                        p = lookup_prices(temp_convert)
                    else:
                        p = lookup_prices(t[1])
                    print("FOUND PRICE: " + str(p[0]))
                    cost = float(p[0]) * float(t[0])
                    self.ingr_cost += cost
                    buy_price = QStandardItem(str(cost))
                    blank_list.append([ingr, qty, buy_price])
                    #blank_list[0].appendRow([ingr,qty,buy_price])
                    # parent.appendRow([
                    #     ingr, qty, buy_price  # ingr col1: qty col2: buy price col3
                    # ])
                except IndexError as e:
                    print("Index Error" + str(i)  + " " + str(t))
                    print(e.args)

        capital = float(self.capital.text())
        self.can_make = math.floor(capital / self.ingr_cost)  # Formulate and set sell quantity ( qty can be made )
        print("******************\n")
        parent = None
        print(blank_list)
        while(len(blank_list)):
            temp_list = []
            total_quant = 0
            total_cost = 0
            new_parent = False
            x = 0
            y = len(blank_list)
            j = 0
            print("LEN BLANK LIST OUTSIDE: " + str(len(blank_list)))
            while x < y:
                print("LEN BLANK LIST INSIDE: " + str(len(blank_list)))
                temp_list = []
                if (not isinstance(blank_list[x], QStandardItem) and len(blank_list[x]) > 1 ):
                    while  j < len(blank_list[x]):
                        print((blank_list[x][j]).text())
                        temp_list.append(blank_list[x][j])
                        j += 1
                    total_quant = self.can_make * int(float((temp_list[1]).text()))
                    total_cost = self.can_make * float((temp_list[2]).text())
                    temp_list.append(QStandardItem(str(total_quant)))
                    temp_list.append(QStandardItem(str(total_cost)))
                    parent.appendRow(temp_list[0:])
                    blank_list.pop(0)
                    y = len(blank_list)
                    j = 0

                else:
                    print(blank_list[x].text())
                    parent = blank_list[x]
                    new_parent = True
                    if new_parent:
                        self.model.appendRow(parent)
                        new_parent = False
                    blank_list.pop(0)
                    y = len(blank_list)
                
        # print(blank_list)
        # while(len(blank_list)):
        #     total_quant = 0
        #     total_cost = 0
        #     temp_list = []
        #     if(len(blank_list) > 1 ):
        #         total_quant = self.can_make * int(float((blank_list[1][1]).text()))
        #         total_cost = self.can_make * float((blank_list[1][2]).text())
        #         print(str(total_quant) + " = " + str(self.can_make) + " * " + (blank_list[1][1]).text())
        #         print(total_cost)
        #         temp_list.append(blank_list[1][0:])
        #         temp_list[0].append(QStandardItem(str(total_quant)))
        #         temp_list[0].append(QStandardItem(str(total_cost)))
        #         blank_list.pop(1)
        #         #print(temp_list)
        #         parent.appendRow(temp_list[0])
        #     self.model.appendRow(blank_list[0])
        #     blank_list.pop(0)
            #self.model.appendColumn([QStandardItem("11235")])

            # while(len(blank_list)):
            #     total_quant = 0
            #     total_cost = 0
            #     temp_list = []
            #     if len(blank_list) > 1:
            #         tot_quant = self.can_make * blank_list[1][2]
            #         total_cost = self.can_make * blank_list[1][3]
            #         blank_list.pop(1)
            #     temp_list = blank_list.pop(0)
            #     temp_list.append(total_quant, total_cost)
            #     self.model.appendRow(temp_list)
            
            print(self.can_make)
            print(self.ingr_cost)

            #self.model.appendRow(parent)
            self.debug_tree.expandAll()
        

    def buy_combo_selected(self):
        item = self.buyCombo.currentText()
        capital = float(self.capital.text())
        can_buy, buy_individual, buy_flip = 0.0, 0.0, 0.0

        p = lookup_prices(item)
        buy_price, sell_price = p[0], p[1]

        can_buy = math.floor(capital / buy_price)
        buy_individual = sell_price * can_buy
        buy_profit = buy_individual - capital
        self.buyQuantity.setText(str(can_buy))
        self.buyIndividual.setText(str(buy_individual))
        self.buyFlip.setText(str(buy_profit))


def lookup_dump_data(item):
    dict = constants.dict
    trans_item = ""
    for piece in dict:
        if item == piece[1]:
            trans_item = piece[0]
            break
    return trans_item


def lookup_prices(item):
    price_list = []
    print("LOOKING FOR: " + item)
    for elem in line_list:
        if item == elem[0]:
            print("FOUND ITEM: " + item)
            price_list.append(float(elem[1]))
            price_list.append(float(elem[2]))
            break
    return price_list


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    line_list = []
    dict = constants.dict

    with open(constants.INGREDIENTS, "r") as read_file:
        lines = read_file.readlines()
    for line in lines:
        as_list = line.split(",")
        line_list.append(as_list)

    app = QtWidgets.QApplication(sys.argv)
    window = Ui()
    window.show()
    app.exec_()
