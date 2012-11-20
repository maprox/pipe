# -*- coding: utf8 -*-
'''
@project   Maprox <http://www.maprox.net>
@info      Falcon answer class from Observer
@copyright 2009-2012, Maprox LLC
'''

# -----------------------------------------------------
class FalconObject(object):
  ''' Falcon object class '''
  def toArray(self):
    pass

# -----------------------------------------------------
class FlaconError(FalconObject):
  '''
  Falcon error class.
  Not used. Deprecated.
  Kept alive for potential further use.
  '''
  __code = 0
  __params = list()

  def __init__(self, code, params):
    self.setCode(code)
    self.setParams(params)

  def setCode(self, value):
    self.__code = value
    return self

  def setParams(self, value):
    self.__params = value
    return self

  def getCode(self):
    return self.__code

  def getParams(self):
    return self.__params

  def toArray(self):
    result = dict()
    result['code'] = self.getCode()
    result['params'] = self.getParams()
    return result

# -----------------------------------------------------
class FalconAnswer(FalconObject):
  ''' Falcon answer class '''
  __errorsArrayForced = False
  __success = False # the result of some operation
  __errors = list() # errors list
  __names = {
    'success': 'success',
    'errors': 'errors'
  }

  def __init__(self, success = True):
    ''' Constructor '''
    self.reset()
    self.setSuccess(success)
    pass

  def reset(self):
    ''' Clear data '''
    self.__success = True
    self.__errors = list()
    return self

  def setSuccess(self, value, clearErrors = False):
    ''' Result value set '''
    if (clearErrors):
      self.reset()
    self.__success = value
    return self

  def getErrorsList(self):
    ''' Returns the list of errors '''
    return self.__errors

  def getLastError(self):
    ''' Returns last error object '''
    errors = self.getErrorsList()
    if (len(errors) > 0):
      return errors[len(errors) - 1]
    return None;

  def isSuccess(self):
    return self.__success

  def isFailure(self):
    return (not self.isSuccess())

  def error(self, code, params = list()):
    self.setSuccess(False)
    self.__errors.append({
      'code': code,
      'params': params
    })
    return self;

  def appendErrors(self, errors):
    for e in errors:
      self.error(e['code'], e['params'])
    return self

  def load(self, data):
    if (not isinstance(data, dict)):
      return self
    if ('success' in data):
      self.setSuccess(data['success'])
    if ('errors' in data):
      self.appendErrors(data['errors'])
    return self

  def toArray(self):
    result = dict()
    result[self.__names['success']] = self.isSuccess()
    if (self.__errorsArrayForced or not self.isSuccess()):
      result[self.__names['errors']] = self.getErrorsList()
    return result
