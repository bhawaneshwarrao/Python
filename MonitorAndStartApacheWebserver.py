import paramiko
import re
import time
import sys
import os
import argparse


class MonitorAndStartApacheWebserver:
    
    def __init__(self) -> None:
        self.output={}
        self.output["start_status"]=False
        self.output["url_status"]=None
        self.output['error']=None

    def Ping(self, server):
        pattern = r"win"
        windows = re.search(pattern, sys.platform)
        try:
            command = ("ping -n 2 " + str(server)) if windows else ("ping -c 2 " + str(server))
            resp = os.system(command)
            return (True if (resp == 0) else False)
        except:
            return False

    def verifyInputs(self,executeContext):
        empty=[]
        
        for key,item in executeContext.items():
            if (len(str(item))<1):
                print ("\nError! "+key+" Cannot be Empty.")
                empty.append(key)
        
        if len(empty)>=1:
            temp=",".join(empty)
            self.output['error']="'"+temp+"' cannot be empty."
            return False   
            
        return True

    def connect(self,hostname, port, username, password):
        print("Connecting to the Server..")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            client.connect(hostname=hostname, port=port,
                           username=username, password=password)
            print("Connected Successfully to the Server..")
            return client
        except Exception as e:
            self.output['error']=str(e)
            return None

    def executeCmd(self,client,command):
        
        try:
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error=stderr.read().decode()

            if len(error)>0 and len(output)<1:
                output=error
            return output
        
        except Exception as e:
            self.output['error']=str(e)
            return None

    def execute(self,executeContext):
        
        checkinputs=self.verifyInputs(executeContext)
        if checkinputs==False:
            return self.output
        
        try:
            
            username=executeContext["username"]
            password=executeContext["password"]
            url= executeContext["url"]
            
            hostname=url.split("/")[2]
            
            port=22
            
            
            self.output['server']=hostname
            self.output['url']=url
            
            status=self.Ping(hostname)
            #status=True  #for local testing
            
            if status==False:
                self.output["error"]="Host is not reachable"
                self.output['url_status']="Invalid"
                return self.output

            
            client=self.connect(hostname,port,username,password)
            
            if client == None:
                return self.output
                
                
            command=f"wget {url}"
            output=self.executeCmd(client,command)

            if "failed: Connection refused" in output:
                
                print("\nServer is in Stopped state. \nStarting the Apache Server...")

                command="sudo systemctl start httpd"
                output=self.executeCmd(client,command)
                
                if client ==None:
                    return self.output
                time.sleep(2)
                
                print("\nChecking Status....")

                command="sudo systemctl status httpd"
                output=self.executeCmd(client,command)
                print(output)
                if client ==None:
                    return self.output
                
                if ("active (running)" in output):
                    
                    self.output["start_status"]=True
                    self.output['apache_status']="Active"
                    
                    print("\nApache Server Started Successfully.\n")
                    self.output['info']="Apache Server Started Successfully."
                    
                    command = f"wget {url}"
                    output = self.executeCmd(client,command)
                    if client ==None:
                        return self.output

                    if "failed: Connection refused" not in output:

                        command=" wget --spider -S "+url+" 2>&1 | grep 'HTTP/' | awk '{print $2}'"
                        output=self.executeCmd(client, command)
                        if client ==None:
                            return self.output
                        
                        self.output["url_status"]=output.split("\n")[0]
                        return self.output

                print("Apache webserver failed to start")
                self.output["error"] = "Apache webserver failed to start"
                self.output['apache_status']="Inactive"
                return self.output

            else:
                print(output)
                self.output["start_status"]=False
                self.output['apache_status']="Active"
                print("\nApache Server is Already In Active State\n")
                self.output["info"] ="Already In Active State"
                
                command="wget --spider -S "+url+" 2>&1 | grep 'HTTP/' | awk '{print $2}'"
                output=self.executeCmd(client,command)
                if client ==None:
                    return self.output
                self.output["url_status"] = output[:-1]
            
                return self.output
            
        except Exception as e:
            print(e)
            self.output["error"]=str(e)
            return self.output


        
if __name__ == '__main__':
    
    obj=MonitorAndStartApacheWebserver()
    
    cli=argparse.ArgumentParser()
    cli.add_argument(dest="user",help="Login Username")
    cli.add_argument(dest="password",help="Login Password")
    cli.add_argument(dest="url",help="URL with the Login Host or IP")
    cli_args=cli.parse_args()
    
    username=cli_args.user
    password=cli_args.password
    url=cli_args.url
    
    context = {"url": url, "username": username, "password": password }
        
    output=obj.execute(context)
    
    print("\nThe Returned Value:")
    print(output,"\n")

