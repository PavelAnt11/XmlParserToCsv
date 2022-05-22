import csv
import sys
from pathlib import Path
from xml.dom.minidom import parseString
import xml.etree.ElementTree as ET
from validate import PeriodHandler, SumHandler, check_format_correct
from log_conf import get_logger


class ConvertXmlToCsv:
    def __init__(self, path_to_xml):
        self.file_path_to_xml = Path(path_to_xml)
        self.full_name_with_ext = self.file_path_to_xml.name
        self.file_name = self.file_path_to_xml.stem
        self.file_extension = self.file_path_to_xml.suffix
        self.path = self.file_path_to_xml.parent
        self.data = dict()
        self.double = set()

    def check_file_extension(self, xml_logger):
        if self.file_extension == '.xml':
            return True
        else:
            xml_logger.critical(f'Ошибка! Невозможно обработать файл {self.full_name_with_ext} Неверное расширение. Должно быть -> .xml')
            if not self.path.joinpath('bad').is_dir():
                self.path.joinpath('bad').mkdir()
            self.file_path_to_xml.replace(self.path / 'bad' / self.full_name_with_ext)
            return False

    def load_xml_tree(self):
        tree = ET.parse(self.file_path_to_xml)
        self.root = tree.getroot()

    def __get_relevance_date(self):
        self.data_relevance_date = (self.root.find('СлЧаст/ОбщСвСч/ИдФайл/ДатаФайл')).text
        return self.data_relevance_date

    def __registry_processing(self):
        static_data = {'имя файла': self.file_name, 'дата файла': self.data_relevance_date}
        for i, child in enumerate(self.root.iter('Плательщик')):
            personal_account = child.find('ЛицСч').text
            FIO = child.find('ФИО').text
            address = child.find('Адрес').text
            period = child.find('Период').text
            summ = child.find('Сумма').text
            row = {**static_data, 'ЛицСч': personal_account, 'ФИО': FIO, 'Адрес': address,
                                 'Период': period, 'сумма': summ}
            if personal_account is None or period is None:
                xml_logger.warning(f'Запись № {i} не имеет одного из ключевых реквизитов')
                continue
            if (personal_account, period) not in self.data:
                self.data[(personal_account, period)] = row
                if data_validate(i, row, xml_logger):
                    xml_logger.info(
                        f'Запись № {i} с лицевым счетом {personal_account} и периодом {period}.Запись валидна')
                else:
                    xml_logger.warning(
                        f'Запись № {i} с лицевым счетом {personal_account} и периодом {period}.Не прошла валидацию.')
            else:
                self.double.add((personal_account, period))
                xml_logger.warning(f'Запись {i} с лицевым счетом {personal_account} \
                 и периодом {period} повторяется. \
                 Все записи с указанными данными не будут добавлены')
        self.data = {k: self.data[k] for k in set(self.data) - self.double}
        return self.data

    def __write_to_csv(self, encoding):
        path_for_csv = self.path.joinpath(self.file_name + '.csv')
        sys.stdout = open(path_for_csv, 'w', encoding=encoding)
        wr = csv.writer(sys.stdout, quoting=csv.QUOTE_NONNUMERIC, delimiter=';')
        for record in self.data.values():
            wr.writerow(record.values())
        xml_logger.info(f'Обработка файла {self.full_name_with_ext} завершена')

    def __move_file_to_arh(self):
        if not self.path.joinpath('arh').is_dir():
            self.path.joinpath('arh').mkdir()
        self.file_path_to_xml.replace(self.path / 'arh' / self.full_name_with_ext)

    def main(self):
        self.load_xml_tree()
        check_format_correct(self.__get_relevance_date(), xml_logger)
        self.__registry_processing()
        encoding = self.__read_encoding()
        self.__write_to_csv(encoding)
        self.__move_file_to_arh()

    def __read_encoding(self):
        with open(self.file_path_to_xml, 'rb') as file:
            declaration = file.readline()
            declaration = str(declaration, 'UTF-8')
            root = parseString(declaration + '<mocktag></mocktag>')
            return root.encoding


def set_log_conf(path):
    if not path.joinpath('log').is_dir():
        path.joinpath('log').mkdir()
    xml_logger = get_logger(__name__, path.joinpath('log'))
    return xml_logger


def data_validate(i, request, xml_logger):
    period = PeriodHandler()
    sumhandler = SumHandler()
    period.set_next(sumhandler)
    return period.handle(i, request, xml_logger)


if __name__ == '__main__':
    file_path_to_xml = sys.argv[1]
    conv = ConvertXmlToCsv(file_path_to_xml)
    xml_logger = set_log_conf(conv.path)
    if conv.check_file_extension(xml_logger):
        conv.main()
