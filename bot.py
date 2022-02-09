from iqoptionapi.stable_api import IQ_Option
from time import time, sleep
from datetime import datetime
from threading import Thread, Lock, get_ident
import os

API = IQ_Option('contato.evertonoliveira@hotmail.com', 'everoliver0582')
API.connect()

API.change_balance('PRACTICE') # PRACTICE / REAL

if API.check_connect() == False:
  print('\n Erro ao se conectar! \n')
  input('Aperte ENTER para sair!')
  exit()
else:
  print('\n Conectado com sucesso! \n')

def dir_log():
  global geral
  
  try:
    dir_fpath = os.path.expanduser(r'~\AppData\Roaming\MetaQuotes\Terminal')
    dir_spath = [dir_fpath + '\\' + d for d in os.listdir( dir_fpath ) if len(d) == 32 ][0]
    geral['dir'] = [dir_spath + '\\' + version + '\\files\\' for version in os.listdir(dir_spath) if 'MQL' in version][0]
  except Exception as e:
    print('Erro no dir_log() ->', e)
    input('\n APERTE ENTER PARA FECHAR \n')
    exit()

def retorno_ex():
  global geral

  try:
    if os.path.isfile(geral['dir'].replace('files','Indicators') + 'Retorno.ex4') == False:
      os.rename('Retorno.ex4', geral['dir'].replace('files', 'Indicators') + 'Retorno.ex4')
  except Exception as e:
    print('\n Não foi possível verificar/mover o arquivo Retorno.ex4\n Erro:', e)
    input('\n APERTE ENTER PARA FECHAR \n')
    exit()

def get_sinal():
  global geral

  sinais = []
  arq_sinais = geral['dir'] + datetime.now().strftime('%Y%m%d') + '_retorno.csv'
  try:
    file = open(arq_sinais, 'r').read()
  except:
    file = open(arq_sinais, 'a').write('\n')
    file = ''

  for index, sinal in enumerate(file.split('\n')):
    if len(sinal) > 0 and sinal != '':
      sinal_ = sinal.split(',')
      #TIMESTAMP, PARIDADE, CALL,1
      if sinal_[0].isdigit():
        if int(int(sinal_[0]) - time()) <= 2:
          sinais.append({'timestamp': sinal_[0],
                          'par': sinal_[1],
                          'dir': sinal_[2],
                          'timeframe': sinal_[3]
                        })
        open(arq_sinais, 'w').write(file.replace(sinal,''))
  return sinais

def entrada(data):
  global API
  global geral

  geral['lock'].acquire()
  geral['ops'].update({get_ident(): {
                                      'entrada': geral['valor'],
                                      'par': str(data['par']).upper(),
                                      'timeframe': int(data['timeframe']),
                                      'dir': str(data['dir']).lower(),
                                      'timestamp': int(data['timestamp']),
                                      'resultado':'',
                                      'lucro':0,
                                      'status':'',
                                      'id': 0,
                                      'op_time': 0 
                                    }
                      })
  geral['lock'].release()

  geral['lock'].acquire()
  try:
    geral['ops'][get_ident()]['status'], geral['ops'][get_ident()]['id'] = API.buy_digital_spot(geral['ops'][get_ident()]['par'], geral['ops'][get_ident()]['entrada'], geral['ops'][get_ident()]['dir'], geral['ops'][get_ident()]['timeframe'])
    geral['ops'][get_ident()]['op_time'] = int(time())
  except Exception as e:
    print('Erro ao abrir a operação ->', e)
    geral['ops'][get_ident()]['status'] = False
    pass

  geral['lock'].release()

  if geral['ops'][get_ident()]['status']:
    geral['ops'][get_ident()]['status'] = False

    while geral['ops'][get_ident()]['status'] == False:
      geral['lock'].acquire()
      geral['ops'][get_ident()]['status'], geral['ops'][get_ident()]['lucro'] = API.check_win_digital_v2(geral['ops'][get_ident()]['id'])
      geral['lock'].release()

    geral['lock'].acquire()
    print('\nHORÁRIO DO SINAL:', datetime.fromtimestamp(int(geral['ops'][get_ident()]['timestamp']).strftime('%H:%M:%S')))
    print('HORÁRIO DA ENTRADA:', datetime.fromtimestamp(int(geral['ops'][get_ident()]['op_time']).strftime('%H:%M:%S')))
    print('DIFERENÇA ENTRE HORÁRIOS:', abs(int(geral['ops'][get_ident()]['op_time']) - int(geral['ops'][get_ident()]['timestamp'])), 'segundos')
    print('PARIDADE:', geral['ops'][get_ident()]['par'])
    print('DIREÇÃO:', geral['ops'][get_ident()]['dir'])
    print('TIMEFRAME:', geral['ops'][get_ident()]['timeframe'])
    print('RESULTADO:', 'WIN' if geral['ops'][get_ident()]['lucro'] > 0 else 'LOSS')
    print('LUCRO:', round(geral['ops'][get_ident()]['lucro'], 2), '\n')
    geral['lock'].release()

  del geral['ops'][get_ident()]

geral = {'dir': '', 'valor': 0.0, 'lock': Lock(), 'ops': {}}
dir_log()
retorno_ex()

geral['valor'] = float(input('\nInsira um valor de entrada: '))
print('\n\n')

try:
  while True:
    sinais = get_sinal()

    if len(sinais) > 0:
      for data in sinais:
        Thread(target=entrada, args=(data, ), daemon=True).start()
    print(len(geral['ops']), 'Operações abertas |', datetime.now().strftime('%H:%M:S'), end='\r')
    sleep(0.5)

except Exception as e:
  print('Código finalizado com erro ->', e)
  exit()