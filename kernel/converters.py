# -*- coding: utf8 -*-
'''
@project   Maprox Observer <http://maprox.net/observer>
@info      Convertion utils
@copyright 2009-2011, Maprox Ltd.
@author    sunsay <box@sunsay.ru>
@link      $HeadURL: http://vcs.maprox.net/svn/observer/Server/trunk/kernel/converters.py $
@version   $Id: converters.py 357 2010-12-17 13:30:30Z sunsay $
'''

def intToBytes(value, size = 0, little_endian = True):
  '''
   Функция преобразования положительного целого числа в массив байт.
   @param[in] value - целое число
   @param[in] size - размер выходного блока данных.
     К примеру, если size = 3, а value = 255 на выходе получим FF 00 00
   @param[in] little_endian - порядок вывода байтов: true [little_endian] 
     - от младшего разряда к старшему, false [big_endian] - наоборот
   @return bytes() последовательность байт
  '''
  result = bytes() # инициализируем переменную, в которую запишем результат

  # собираем байты (в обратном порядке)
  while value > 0:
    tail = bytes([value % 0x100]) # запомним остаток от деления на 256
    if little_endian: # в зависимости от порядка вывода, прибавляем остаток
      result += tail  # либо в конец последовательности
    else:             # либо в начало
      result = tail + result;
    value >>= 8 # смещаемся на 8 бит вправо

  # увеличиваем последовательность до нужного размера
  while len(result) < size:
    if little_endian: # в зависимости от порядка вывода, 
      result += b'\x00'  # добавляем нулевой байт в конец последовательности
    else:             # либо в начало
      result = b'\x00' + result

  # отдаём результат просящему
  return result