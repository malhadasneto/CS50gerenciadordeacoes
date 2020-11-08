
Hi all!

Welcome to my CS50 Final Project: "Easy Tax B3".

I have developed this web app for traders who operate in the Brazilian stock market - [B]³, previously known as BVMF.  According to the federal laws, people whose operations in a single month exceed R$20,000 (twenty thousand reais) must pay taxes over profit –15% for regular trades. Daytrades are always taxed in 20%. 
The problem is: rules can be tricky and there is no official service where traders can check the amount to be paid. Yes, humans are going to Mars but traders have to calculate (and pay) taxes by themselves. And for each mistake or miscalculation made, the government will charge a penalty fee during the period of the Income Tax Return.
For a fee, some stock exchange agencies will offer the service, while others prefer to avoid taking any responsibility for that. As a small trader myself, I know that each cent saved is a cent to be invested. So I decided to start this app.
As inspiration and the starting point, I have been using a Google Spreadsheet made by Carteira Rica team (https://carteirarica.com.br/carteira-de-acoes/)  for 6 months now. I miss especially a feature to help me with day trades, so I am really glad that I´ve found a way to add this feature to my app.
For purposes of practicing what I learned during the CS50 Course, I wrote the program in Flask/Python and Sqlite3. I am using the login/hash system provided by the course for the “Finance” project, with some minor improvements like a “reset password” option.

How to use the app? It is very simple:

•	Register an email and password (password isn't stored in plain text)
•	Register every buy/sell operation.
    o    Next, the system will check if the stock code is valid:
        	1: comparing to our database.
        	2: if not in our db, it´ll check on Google.
            •	Path A: Code is found, probably a company has made an IPO after the launch of this app, so the system will add it to our database.
            •	Path B: Code is not found, user will be asked to check the information.
•	Lastly, user must register all the expenses for each day of operation in the stock exchange, such as brokerage, tax in advance, emoluments, stock agency fee, etc.
    o	This is important because for tax calculation purposes, the profit must be calculated using the “gross” (sale less purchase price), minus operational expenses.  

Let´s highlight the features of this web app!

•	It’s free.
•	Users can see the history of operations.
•	Users can follow his/her stocks with current performance.
•	Tax calculation:
    o	The app understands when trades are regular or day trades, and apply the correct tax percentage.
    o	The app remembers “bad months”, so losses can be used to reduce tax from profitable months.
•	The app will inform user how much tax is to be paid each month.

What was the biggest challenges?

Probably I missed an easy way to do that, but it´s done now.

•	Level Easy:
    o	Example: yesterday, a trader bought 1.000 “xpto” stocks and today sold 1.000 “xpto”.

•	Level Hard:
    o	User already had 500 “xpto” on balance. Yesterday, he bought 300 "xpto" more, and sold 400.
    o	This trader has to pay 20% tax over the 300 units bought/sold in the same day.
    o	Also, he has to pay 15% over 100un (he sold 100un from an old stock of 500 un). It is important to notice that system must uses the purchasing value of the day of the previous operation. 
    o	Finally, this trader is going to keep on balance 400 units of “xpto”. However, stocks will have their purchased price changed to the average!

Important. I would like to apologize for my web app in PT-BR. When I started the project, I thought that only Brazilians would be interested in the app. Later I realized that some foreigner living here could have the same problem I have. So, in the future I may be launching an English version. If you want it now, please let me know!

Finally, I would like to thank Harvard and Mr. David J. Malan for such amazing classes. Also, thanks to the team for all the tutorials, especially the one for the dictionary challenge in C.

And, most of all, I am grateful for the courage they gave me to start this late change in my professional life!

I hope you enjoy my app. If you find any errors, please let me know (zaninmalhadas@gmail.com)! See ya!