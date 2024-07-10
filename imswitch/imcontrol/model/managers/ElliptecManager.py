from imswitch.imcommon.model import initLogger
from abc import ABC, abstractmethod
import elliptec

# ______________ UNTESTED _________________
class ElliptecSlider(ABC):
    def __init__(self, sliderInfo, name:str):
        self.__logger = initLogger(self)
        self.__port = sliderInfo.managerProperties['port']
        self.__sliderInfo = sliderInfo
        self.__name = name

        # initialise
        try:
            self._ell9 = elliptec.Slider(elliptec.Controller(self.__port))
            self.__logger.debug(f'Initialized ELL9 slider on port {self.__port}, homing device.')
            self._ell9.home()
        except:
            self.__logger.error(f'Failed to initialize ELL9 slider on port {self.__port}.')

    def home(self):
        self.__logger.error(f'Homing ELL9.')
        self._ell9.home()

    def move(self, direction:str):
        self.__logger.debug(f'Moving ELL9 {direction}.')
        self._ell9.move(direction)

    def setPosition(self, position:int):
        self.__logger.debug(f'Setting ELL9 position to {position}.')
        self._ell9.set_slot(position)

