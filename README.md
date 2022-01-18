# Finance

Finance is a Flask web app that allows users to register for an account, query real stocks’ actual prices (data from IEX) and the value of stocks owned, and conduct transactions (buy and sell stocks). I generated a database on the backend using SQLite to store account and stocks information, transaction history, and each user's stocks portfolio. 


To run this program, ensure that you have all requirements in requirements.txt. You must also obtain an API key from IEX Cloud, the service used to get the stock information. If you don't already have an API key from IEX Cloud, you can register for an account at https://iexcloud.io/cloud-login#/register to generate a public API. In your terminal, excute:

    $ export API_KEY=value
    $ flask run

The "value" in "export API_KEY=value" is the public or publishable API key from IEX. The web application will launch on the local host at 5000 port. Please see the link below for a demo of the web application.


# Walkthrough/Demo

https://harvard.zoom.us/rec/share/4Fwnqlbh1R4Yz8ktTdJYxbuHRpo1HzxjG6XK_h3cJd7DbHuI1CwrkDkDJzdgahMF.0HtbXmRMT-MY8Zv_?startTime=1642489498000
