import os
import platform

from PyQt5 import QtGui, QtWidgets
from src.Controller.PathHandler import resource_path

class FontService:

	_instance = None

	def __init__(self):
		cwd = os.getcwd()
		current_os = platform.system()
		path_to_fonts = cwd 
		if(current_os == 'Windows'):
			path_to_fonts += '\\src\\res\\fonts\\'
		else:
			path_to_fonts += '/res/fonts/'
		path_to_fonts += current_os
		print(" *** Importing fonts: *** ")
		for root, dirs, files in os.walk(path_to_fonts):
			for font_file in files:
				QtGui.QFontDatabase.addApplicationFont(resource_path(os.path.join(root, font_file)))
				print("Added font: " + font_file)
		print(" *** Imported fonts *** \n\n\n")

	def get_instance():
		if(FontService._instance == None):
			FontService._instance = FontService()
		return FontService._instance

	def get_scaled_font_pixel_size(self, main_app, original_font_size):
		if(type(main_app) != QtWidgets.QApplication):
			print("QApplication not found! Please create it first!")
			return None
		font_pixel_size = original_font_size * main_app.primaryScreen().physicalDotsPerInch()
		current_os = platform.system()
		if(current_os == 'Windows'):
			font_pixel_size /= 96 # Font on Windows should be displayed around 96 DPI
		elif(current_os == 'Linux'):
			font_pixel_size /= 96 # To be decided which DPI is most suited on Linux system
		elif(current_os == 'Darwin'):
			font_pixel_size /= 72 # Font on MacOS should be displayed around 72 DPI
		return int(font_pixel_size)


	def font_family(self):
		current_os = platform.system()
		if(current_os == 'Windows'):
			return 'Segoe UI'
		elif(current_os == 'Linux'):
			return 'Roboto'
		elif(current_os == 'Darwin'):
			return 'HelveticaNeue'