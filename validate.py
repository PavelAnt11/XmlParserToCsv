from abc import ABC, abstractmethod
import datetime


class DataValidateHandler(ABC):
    @abstractmethod
    def set_next(self, handler):
        pass

    @abstractmethod
    def handle(self, i, request, xml_logger):
        pass


class BaseDataHandler(DataValidateHandler):
    _next_handler = None

    def set_next(self, handler):
        self._next_handler = handler
        return handler

    @abstractmethod
    def handle(self, i, request, xml_logger):
        if self._next_handler:
            return self._next_handler.handle(i, request, xml_logger)


class PeriodHandler(BaseDataHandler):
    """проверка на корректность формата Периода"""
    def handle(self, i, request, xml_logger):
        try:
            period = request['Период']
            datetime.datetime.strptime(period, '%m%Y')
            return super().handle(i=i, request=request, xml_logger=xml_logger)
        except ValueError:
            xml_logger.warning(f'Запись № {i} В поле Период Дата неверного формата')
            return False


class SumHandler(BaseDataHandler):
    """Контроль суммы если запись прошла проверку на формат."""
    def handle(self, i, request, xml_logger):
        summ = request['сумма']
        try:
            float(summ)
        except ValueError :
            xml_logger.warning(f'Запись № {i} поле Сумма неверного формата')
            return False
        except TypeError:
            xml_logger.info(f'Запись № {i} поле Сумма - пустое')
            request['сумма'] = ''
            return True
        if float(summ) < 0:
            xml_logger.warning(f'Запись № {i} Сумма не может быть отрицательная. Сумма = {summ}')
            return False
        elif float(summ) == 0:
            xml_logger.warning(f'Запись № {i} Сумма не может быть равна нулю. Сумма = {summ}')
            return False
        else:
            request['сумма'] = "{:.2f}".format(float(summ))
            return True


def check_format_correct(data, xml_logger):
    """Проверяем формат Даты из'СлЧаст/ОбщСвСч/ИдФайл/ДатаФайл'
    Обработку файла не останавливаем. Но если дата не формат указывается в логе"""
    try:
        datetime.datetime.strptime(data, '%d.%m.%Y')
    except ValueError:
        xml_logger.warning(f'Внимание! Дата актуальности данных не верного формата.')
