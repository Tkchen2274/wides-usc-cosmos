import Tkinter as tk
import matplotlib
from matplotlib import pyplot as plt
from matplotlib import animation as animation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import rcParams
rcParams.update({'figure.autolayout': True})
matplotlib.use("TkAgg")
from matplotlib import style
from random import randint
import sys
import FuncThread as FT
import time
import Variables as var


class PlotFrame(tk.Frame):
	def __init__(self,root, rxController, txController, *args, **kwargs):
		tk.Frame.__init__(self, root, *args, **kwargs)
		self.rxController = rxController
		self.txController = txController
		self.rxEderTempData = [0]*var._LIST_LENGTH
		self.txEderTempData = [0]*var._LIST_LENGTH

		self.rxPcbData = [0]*var._LIST_LENGTH
		self.txPcbData = [0]*var._LIST_LENGTH
		rxCol = "darkorange"
		txCol = "blue"
		self.xdata = range(var._LIST_LENGTH)
                #print style.available
		#style.use('fivethirtyeight')
                #style.use('seaborn')
                #style.use('classic')
                #style.use('bmh')
                style.use('ggplot')
		
		# Chip Temp
		self.chipFig = plt.figure()
		self.chipFig.set_size_inches(4,2)
		self.chipTempAx = self.chipFig.add_subplot(1,1,1)
                
		self.chipTempAx.set_ylabel('Chip Temp (deg. C)', fontsize=var._FONTSIZE, rotation='horizontal')
		self.chipTempAx.yaxis.set_label_coords(0,1.02)
		self.chipTempAx.set_xticklabels([])
		#self.rxTempLine, = self.chipTempAx.plot(self.xdata, self.rxEderTempData, color=rxCol, label="RX", linewidth=2.0)
		self.txTempLine, = self.chipTempAx.plot(self.xdata, self.txEderTempData, color=txCol, linewidth=2.0)
		plt.legend(loc=2, fontsize=var._FONTSIZE)

		# Pcb Temp
		self.pcbFig = plt.figure()
		self.pcbFig.set_size_inches(4,2)
		self.pcbTempAx = self.pcbFig.add_subplot(1,1,1)
		self.pcbTempAx.set_ylabel('Pcb Temp (deg. C)', fontsize=var._FONTSIZE, rotation='horizontal')
		self.pcbTempAx.yaxis.set_label_coords(0,1.02)
		self.pcbTempAx.set_xticklabels([])
		#self.rxPcbline, = self.pcbTempAx.plot(self.xdata, self.rxPcbData, color=rxCol, label="RX", linewidth=2.0)
		self.txPcbLine, = self.pcbTempAx.plot(self.xdata, self.txPcbData, color=txCol, linewidth=2.0)

		for label in self.chipTempAx.get_yticklabels() + self.pcbTempAx.get_yticklabels():
			label.set_fontsize(var._FONTSIZE)


		self.canvas = FigureCanvasTkAgg(self.chipFig, master=self)
		self.canvas.get_tk_widget().pack(side="left",fill="x", expand=True)
		self.canvas = FigureCanvasTkAgg(self.pcbFig, master=self)
		self.canvas.get_tk_widget().pack(side="left",fill="x", expand=True)

		plt.legend(loc=2, fontsize=var._FONTSIZE)

		self.ybottom = -1
		self.ytop = 30
		self.anims = []

		#self.chipTempAx.set_ylim(self.ybottom, self.ytop)
		#self.pcbTempAx.set_ylim(self.ybottom, self.ytop)


	def _readForPlotChip(self):
		#return self.rxController.getTemp()-273.13, self.txController.getTemp()-273.13
                return 0, self.rxController.getTemp()-273.13
		#return randint(0,9)

	def _readForPlotPcb(self):
                #return self.rxController.getPcbTemp(),  self.txController.getPcbTemp()
                return 0, self.rxController.getPcbTemp()
		#return randint(0,9)

	def _shiftListChip(self):
		self.rxEderTempData = self.rxEderTempData[-var._LIST_LENGTH+1:]
		self.txEderTempData = self.txEderTempData[-var._LIST_LENGTH+1:]

	def _shiftListPcb(self):
		self.rxPcbData = self.rxPcbData[-var._LIST_LENGTH+1:]
		self.txPcbData = self.txPcbData[-var._LIST_LENGTH+1:]

	def startPlotThread(self):
		self.anims.append(animation.FuncAnimation(self.chipFig, self.animateChip, interval=var._GRAPHUPDATEDELAY))
		self.anims.append(animation.FuncAnimation(self.pcbFig, self.animatePcb, interval=var._GRAPHUPDATEDELAY))


	def animateChip(self, i):
		self._shiftListChip()
		rxRead, txRead = self._readForPlotChip()
		#self.rxEderTempData.append(rxRead)
		self.txEderTempData.append(txRead)

		#self.rxTempLine.set_ydata(self.rxEderTempData)
		self.txTempLine.set_ydata(self.txEderTempData)
		
		maxRead = max(rxRead,txRead)
		if maxRead > self.ytop:
			self.ytop = maxRead
			#self.chipTempAx.set_ylim(self.ybottom, self.ytop+20)
                        self.chipTempAx.set_ylim(self.ybottom, 155)
		else:
			#self.chipTempAx.set_ylim(self.ybottom,self.ytop+20)
                        self.chipTempAx.set_ylim(self.ybottom, 155)
		


	def animatePcb(self, i):
		self._shiftListPcb()
		rxPcbRead, txPcbRead = self._readForPlotPcb()
		#self.rxPcbData.append(rxPcbRead)
		self.txPcbData.append(txPcbRead)

		#self.rxPcbline.set_ydata(self.rxPcbData)
		self.txPcbLine.set_ydata(self.txPcbData)

		maxRead = max(rxPcbRead,txPcbRead)
		if maxRead > self.ytop:
			self.ytop = maxRead
			#self.pcbTempAx.set_ylim(self.ybottom, self.ytop+20)
                        self.pcbTempAx.set_ylim(self.ybottom, 155)
		else:
			#self.pcbTempAx.set_ylim(self.ybottom,self.ytop+20)
                        self.pcbTempAx.set_ylim(self.ybottom, 155)
		

	def close(self):
		for anim in self.anims:
			anim.event_source.stop()
			anim = 0

		plt.close()
		

if __name__ == "__main__":
	#import controller
	#controller = controller.Controller()
	root = tk.Tk()
	frame = PlotFrame(root)
	frame.ani = animation.FuncAnimation(fig=frame.chipFig, func=frame.animate, interval=100)
	root.mainloop()
	




