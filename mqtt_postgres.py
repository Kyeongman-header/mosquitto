import paho.mqtt.client as mqtt
import psycopg2 as pg2
import datetime
import os
import json

HOST='localhost'
USER='subscriber'
PASSWORD='mypassword'
PORT=1883
TOPIC='auton/airfilter'
QOS=1

DB_HOST='10.0.10.161'
DB='iot'
DB_USER='auton'
DB_PASSWORD='mypassword'

def postgres_machine_add(host,user,password,db,car_number,machine_id):
    try:
        conn=pg2.connect(host=host,dbname=db,user=user,password=password)
    except Exception as e:
        with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
            log.write("-----------------\n postgre sql connection error :( \n ---------------------")
            log.write(e + '\n')
        return
    cur=conn.cursor()
    query=f"INSERT INTO airfilter_machine(id,car_number,pub_date) VALUES ({machine_id}, {car_number},current_timestamp)"
    try :
        cur.execute("INSERT INTO airfilter_machine(id,car_number,pub_date) VALUES (%s, %s,current_timestamp)\n",(str(machine_id),str(car_number)))
        conn.commit()
    except pg2.DatabaseError as dberror:
        with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
            log.write("-----------------------\n insert query to machine table error :(\n ----------------------\n")
            log.write(dberror + '\n')
            conn.rollback()
    else :
        with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
            log.write("insert success \n")
            log.write(query + '\n')
            
    conn.close()

def postgres_sensor_insert(host,user,password,db,sensor,machine_id):
    try:
        conn=pg2.connect(host=host,dbname=db,user=user,password=password)
    except Exception as e:
        with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
            with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
                log.write("-----------------\n postgre sql connection error :(\n--------------------\n")
                log.write(e + '\n')
        return

    cur=conn.cursor()
    n=datetime.datetime.now()
    query=f"INSERT INTO airfilter_sensor (machine_id,sensor,pub_date) VALUES ('{machine_id}', '{sensor}',current_timestamp)"
    
    try :
        cur.execute("INSERT INTO airfilter_sensor (machine_id,sensor,pub_date) VALUES (%s, %s, current_timestamp)\n",(str(machine_id),str(sensor)))
        conn.commit()
    except pg2.DatabaseError as dberror:
        with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
            log.write("------------------------\ninsert query to sensor table error :(\n-----------------------\n")
            log.write(dberror + '\n')
            conn.rollback()
    else :
        with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
            log.write("insert success : \n")
            log.write(query + '\n')

    conn.close()

    

def on_connect(client,userdata,flags,rc):
    client.subscribe(TOPIC,QOS)
    with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
        log.write("connection,subscribe success. "+ str(flags)+ "result code : " + str(rc) + '\n')
        log.write(str(datetime.datetime.now()) + '\n')
    

def on_disconnect(client, userdata, flags, rc=0):
    with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
        log.write("disconnection success. "+str(flags)+ "result code : " + str(rc) + '\n')
        log.write(str(datetime.datetime.now()) + '\n')


def on_message(client,userdata,msg):
    
    # 실제로는 json data로 받고 sensor와 car_number를 더 쉽게 파싱할 수 있음.
    # 지금은 0 번째 숫자로 추가인지 아닌지 가리고, 1,2번째 숫자가 sensor값(혹은 차 넘버),
    #3번째 숫자가 machine 고유 번호임.
    with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
        
        data=str(msg.payload.decode("utf-8"))

        log.write(data + '\n')
        
        try :
                  j=json.loads(data)
        except :
                  log.write("Wrong Format. Try again.\n")
        
        else :
            is_add=j["is_add"]
            sensor=j["sensor"]
            machine_id=j["machine"]
            car_number=j["car_number"]
        
#            shell = 'curl -d ' + "'" + json.dumps({ "machine" : machine_id , "sensor" : sensor }) + "'" + ' -H "Content-Type: application/json" -H "Authorization: Token ef00282ec7f582a7f3500952c6385b6de9b0de94" -X POST https://auton-iot.com/mqtt_postgres/'
#            log.write(shell + '\n')
#            output=stream.read()
#            log.write(output + '\n')
# 고등기술연구원과 테스트가 끝나면, 해당 코드를 실험해볼것.
            
            if is_add==1:
           

                postgres_machine_add(DB_HOST,DB_USER,DB_PASSWORD,DB,car_number,machine_id)
            # 현재 알 수 없는 오류로 postgres 에 insert가 실패할 시 이 client도 연결이 끊김.(재루프.)
            # 당장은 기능 자체에 문제는 없지만 이 경우 장기적으로 버그를 발생시킬 가능성이 있음.
            # 또한 보안적인 문제 때문에라도 결국은 rest api로 갈아타야 함.


            else :

                postgres_sensor_insert(DB_HOST,DB_USER,DB_PASSWORD,DB,json.dumps(sensor),machine_id)

    
        log.write(str(datetime.datetime.now()) + '\n')

            
client=mqtt.Client()
client.on_connect=on_connect
client.on_disconnect=on_disconnect
client.on_message=on_message
client.username_pw_set(username=USER,password=PASSWORD)
client.connect(HOST,PORT,)

client.loop_forever()

with open("/home/ubuntu/mqtt_postgres.log",'a') as log :
    log.write("end of python code.\n")
    log.write(str(datetime.datetime.now()) + '\n')
    log.close()
