import pathlib
import platform
import logging
from src.Controller.PathHandler import resource_path

class StyleSheetReader:
    """
    A class to hold the style sheet data to be used in the User Interface classes.
    As this information will need to be used for most of the User Interfaces
    This class is intended to reduce the number of times the style sheet is read
    """

    style_sheet: str = None

    def __init__(self) -> None:
        """
        Initialising the StyleSheetReader and getting the data from the style sheet
        :rtype: None
        """
        logging.info("Initialising the StyleSheetReader and getting the style sheet")
        if StyleSheetReader.style_sheet is None:
            StyleSheetReader.style_sheet = self._get_layout_data()
            logging.info("StyleSheetReader has Readd file")
        if StyleSheetReader.style_sheet is None:
            logging.error("StyleSheetReader did Not Read file")
            raise ValueError("No StyleSheet")

    def get_stylesheet(self) -> str:
        """
        Returns the Stylesheet static member
        :rtype: str
        """
        logging.info("Getting the Stylesheet static member")
        return StyleSheetReader.style_sheet

    def _get_platform_stylesheet(self, running_platform: str) -> str:
        """
        Determining which version of the Style sheet to use based on the platform running the program
        :param running_platform:
        :return:
        :rtype: str
        """
        logging.info("Getting the Platform specific style sheet location")
        if running_platform == "Darwin":
            logging.info("Getting the Darwin style sheet location")
            return "res/stylesheet.qss"
        else:
            logging.info("Getting the Win/Linux style sheet location")
            return "res/stylesheet-win-linux.qss"

    def _get_layout_data(self) -> str:
        """
        Reading the style sheet for the User Interface and loading it into the style_sheet member
        :rtype: str
        """
        logging.info("Reading the style sheet for the User Interface")
        path_stylesheet = self._get_platform_stylesheet(platform.system())
        return pathlib.Path(resource_path(path_stylesheet)).read_text()