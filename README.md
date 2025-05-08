How to Run (README):
To run our program, perform the following steps:
1.  Download the source code from the GitHub repository using the prototype branch.
2.  Inside the config folder, in the .env file, paste the provided STEAM_API_KEY value provided in the submission/report (omitted here so nobody else can use the API key)
3.  In the terminal, run pip install -r requirements.txt to install all of the dependencies required to run the program.
4.  To run the regular client, run the testclient script with python testclient.py

    a. There are options listed where 1 is for profile summary, 2 is for the user’s game list, 3 is for the user’s friend list, 4 is for game recommendations, and q           is to quit.
    
    b. For sample user ids, see the list of user ids steam_ids.txt

5.  To run the benchmarked client, run the benchmark_friend_workloads script with python benchmark_friend_workloads.py (this script will take about a minute or 2 to run, so please be patient)

   a.   To view the results of the benchmarking for yourself, look inside the benchmarks folder that will be generated after running the script.
6. The program will require some disk space to work properly, as it uses JSON files to cache data received from the Steam API.
