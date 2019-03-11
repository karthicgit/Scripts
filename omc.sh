#!/bin/bash
usage()
{
 echo "This script will copy all files mentioned in upload.txt from local server to remote server"
 echo "Example content of upload.txt"
 echo "============================="
 echo "/tmp/*.trc"
 echo "/tmp/alert.log"
 echo "/home/opc/cataline.log"
 echo "============================="
 echo "Usage: $0 <path where upload.txt is present and countfile gets created> <remoteserver> <remoteserverpath>Example: ./omc.sh /tmp 10.10.10.10 /tmp"
 exit 1
}
if [ $# -eq 0 ]
then
    usage
fi
#loop starts
uploadfile=$1/upload.txt
countpath=$1 
while true
do
 #counter set to 0
 intcount=0
 #put the list of files you want to upload in $uploadfile
 for f in `cat $uploadfile`
 do
  intcount=`expr $intcount + 1`
  #extracting filename 
  filename=`basename $f`
  #setting filename
  newfile="newfiledontdelete"
  #setting countfile name
  countfile="countfiledontdelete"
  #check if countfile exists and create if does not exist
  if [ ! -f $countpath/$countfile ]
  then
    touch $countpath/$countfile
  fi
  tt=`sed -n "/$filename/p" $countpath/$countfile`
  #count to check number of files to upload
  if [ -z "$tt" ]
  then
   count=`wc -l < $f`
   echo $count"_"$filename >> $countpath/$countfile
   sed -n 1,"$count"p $f > $countpath/$newfile;
   #use your own scp commands to transfer files.
   sshpass -p 'password' scp $countpath/$newfile oracle@$2:$3/$filename
  fi
  #tailcount=`wc -l < /tmp/$countfile`
  taillcount=`expr $intcount - 1`
  if [[ ! -z "$tt" ]]
  then
   count=`sed -n "/$filename/p" $countpath/$countfile|cut -d_ -f1`
  fi
  count1=`wc -l < $f`;
   
  #only when 1000 lines has been added the files get transferred. Change this number accordingly.
  if [ `expr $count1 - $count` -gt 1000 ] 
  then  
	sed -n `expr "$count" + 1`,"$count1"p $f >> $countpath/$newfile;
        oldcount=$count"_"$filename
        newcount=$count1"_"$filename
        sed -i "s/$oldcount/$newcount/" $countpath/$countfile
		#use your own scp commands to transfer files.
        sshpass -p 'password' scp $countpath/$newfile oracle@$2:$3/$filename
  fi
 done;
#wait for 5 minutes. Change this sleep time accordingly.
sleep 300
done;
