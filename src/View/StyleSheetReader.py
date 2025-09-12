import pathlib
import platform
import logging
import functools

from src.Controller.PathHandler import resource_path

logger = logging.getLogger(__name__)

class StyleSheetReader:
    """
    A class to hold the style sheet data to be used in the User Interface classes.
    As this information will need to be used for most of the User Interfaces
    This class is intended to reduce the number of times the style sheet is read
    """

    # The intention of this class is to break up the function into smaller parts while also
    # being a way of telling future users that this group of functions are related

    @functools.lru_cache(maxsize=128, typed=False)
    def get_stylesheet(self) -> str:
        """
        Returns the Stylesheet data
        :rtype: str
        """
        logging.debug("Getting the Stylesheet data")
        style_sheet = self._init_StyleSheetReader()
        return style_sheet

    def _init_StyleSheetReader(self) -> str:
        """
        Determining if a StyleSheet has been read
        :rtype: None
        """
        logger.debug("Initialising the StyleSheetReader and getting the style sheet")
        style_sheet = self._get_layout_data()
        if style_sheet is None:
            logger.debug("StyleSheetReader did Not Read file")
            raise ValueError("No StyleSheet")
        return style_sheet

    def _get_platform_stylesheet(self, running_platform: str) -> str:
        """
        Determining which version of the Style sheet to use based on the platform running the program
        :param running_platform:
        :return:
        :rtype: str
        """
        logging.debug("Getting the Platform specific style sheet location")
        if running_platform == "Darwin":
            logging.debug("Getting the Darwin style sheet location")
            return "res/stylesheet.qss"
        else:
            logging.debug("Getting the Win/Linux style sheet location")
            return "res/stylesheet-win-linux.qss"

    def _get_layout_data(self) -> str:
        """
        Reading the style sheet for the User Interface and loading it into the style_sheet member
        :rtype: str
        """
        logging.debug("Reading the style sheet for the User Interface")
        path_stylesheet = self._get_platform_stylesheet(platform.system())
        return pathlib.Path(resource_path(path_stylesheet)).read_text()