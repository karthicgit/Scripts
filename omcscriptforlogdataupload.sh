#!/bin/bash
while true
do
 #put the list of files you want to upload in upload.txt
 for f in `cat upload.txt`
 do
  filename=`basename $f`
  newfile=$filename"_new"
  countfile=$filename"_count"
  if [ ! -f $newfile ]
  then
   count=`wc -l < $filename`
   echo $count > /tmp/$countfile
   sed -n 1,"$count"p $filename > $newfile;
   #use your own scp commands to transfer files.
   sshpass -p 'password' scp $newfile userid@remotehost:/tmp/$filename
  fi
  count=`head -1 /tmp/$countfile`
  count1=`wc -l < $filename`; 
  #only when 100 lines has been added the files get transferred
  if [ -f $newfile ] && [ `expr $count1 - $count` -gt 100 ] 
  then  
	sed -n `expr "$count" + 1`,"$count1"p $filename > $newfile;
        echo $count1 > /tmp/$countfile;
        sshpass -p 'password' scp $newfile userid@remotehost:/tmp/$filename
  fi
 done;
#wait for 5 minutes
sleep 600
done;
