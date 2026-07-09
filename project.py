import pandas, sys, os, unicodedata, re, requests
def main():
    
    basePath = getPath()

    viewingDF = pandas.read_csv(os.path.join(basePath, "CONTENT_INTERACTION", "ViewingActivity.csv"))
    billingDF = pandas.read_csv(os.path.join(basePath, "PAYMENT_AND_BILLING", "BillingHistory.csv"))

    selector(viewingDF, billingDF)

def selector(viewingDF, billingDF):

    menuOptions = ["All Profiles"] + sorted(viewingDF["Profile Name"].unique())

    while True:

        print("Select your profile:")

        for i, profile in enumerate(menuOptions, start=1):
            print(f"{i}. {profile}")

        choice = input("\nI'm ")
        print()

        lenMenuOptions = len(menuOptions)

        if not choice.isdigit():
            print(f"\nPlease enter a number\n")
            continue

        choice = int(choice)
        
        if not 1 <= choice <= lenMenuOptions:
            print(f"\nPlease enter a number between 1 and {lenMenuOptions}\n")
            continue
        
        selectedProfile = menuOptions[choice - 1]

        while True:

            print(
                "Run an analysis!\n"
                "1 - Total spent\n"
                "2 - Most watched series\n"
                "3 - Most watched movies\n"
                "4 - Total watch time\n"
                "5 - Cost per hour watched\n"
                "6 - Return to profile selection\n"
                "7 - Exit\n"
                )

            selection = input("Run ")

            if not selection.isdigit():
                print(f"\nPlease enter a number\n")
                continue

            selection = int(selection)
            
            if not 1 <= selection <= 7:
                print(f"Please enter a number between 1 and 7\n")
                continue
            
            print()

            match selection:
                case 1:
                    getTotalSpent(billingDF)

                    print("\nPress enter to continue ")
                    input()

                case 2: 
                    result = mostWatchedSeries(viewingDF, selectedProfile)

                    for i, (name, seconds) in enumerate(result.items(), start=1):
                        h = seconds // 3600
                        m = (seconds % 3600) // 60

                        print(f"{i}. {name} — {h}h {m}m")
                    
                    print("\nPress enter to continue ")
                    input()

                case 3:
                    result = mostWatchedMovies(viewingDF, selectedProfile)

                    for i, (name, seconds) in enumerate(result.items(), start=1):
                        h = seconds // 3600
                        m = (seconds % 3600) // 60

                        print(f"{i}. {name} — {h}h {m}m")

                    print("\nPress enter to continue ")
                    input()

                case 4:
                    result = totalWatchTime(viewingDF, selectedProfile)

                    print(result)

                    print("\nPress enter to continue ")
                    input()

                case 5:
                    result = costPerHourWatched(viewingDF, billingDF, selectedProfile)

                    print(result)

                    print("\nPress enter to continue ")
                    input()

                case 6:
                    break
                case 7:
                    sys.exit("Goodbye!\n")
                case _:
                    continue
                    
            


def getPath():

    if len(sys.argv) > 2:
        sys.exit("Invalid arguments")

    if not len(sys.argv) == 2:
        return input("Enter your Netflix data folder path.\n"
                    r"Example: C:\Users\evanc\Downloads\1343059170"
                     "\nPath: ").strip()
    else:
        return sys.argv[1]
    
def clean_title(title):

    title = unicodedata.normalize("NFKD", title)

    title = re.sub(r"[\u02D0\u02F8\u0589\u05C3\u2236\uFF1A]", ":", title)

    title = re.sub(r"\s+", " ", title)

    title = title.strip().rstrip(":")
    return title

def filterRealViews(viewingDF):

    viewingDF = viewingDF.copy()

    if "Supplemental Video Type" in viewingDF.columns:
        mask = viewingDF["Supplemental Video Type"].str.contains("HOOK|TRAILER", na=False)
        viewingDF = viewingDF[~mask]

    return viewingDF

def parseDuration(durationStr):

    h, m, s = durationStr.split(":")

    return int(h) * 3600 + int(m) * 60 + int(s)

def totalWatchTime(viewingDF, selectedProfile):

    viewingDF = filterRealViews(viewingDF)

    if not selectedProfile == "All Profiles":
        viewingDF = viewingDF[viewingDF["Profile Name"] == selectedProfile]

    seconds = viewingDF["Duration"].apply(parseDuration).sum()
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"

def costPerHourWatched(viewingDF, billingDF, selectedProfile):

    viewingDF = filterRealViews(viewingDF)

    if selectedProfile != "All Profiles":
        viewingDF = viewingDF[viewingDF["Profile Name"] == selectedProfile]
    
    seconds = viewingDF["Duration"].apply(parseDuration).sum()
    hours = seconds / 3600
    total = billingDF["Gross Sale Amt"].sum()
    return f"${total / hours:.2f}/hr"

def getTotalSpent(billingDF):

    total = billingDF["Gross Sale Amt"].sum()

    print(f"${total:.2f} USD\n")

    if input("Convert to PYG? (y/n) ").lower() == "y":

        try:
            response = requests.get("https://open.er-api.com/v6/latest/USD", timeout=5)
            data = response.json()
            rate = data["rates"]["PYG"]
            pyg = round(total * rate, 2)
            print(f"\n₲{pyg:,.0f} PYG")

        except Exception:
            print("Couldn't fetch rate. Try again later.")

def mostWatchedSeries(viewingDF, selectedProfile, top_n=5):

    viewingDF = filterRealViews(viewingDF)
    viewingDF = viewingDF[viewingDF["Title"].str.contains(f"Episode|episodio", na=False)]

    if not selectedProfile == "All Profiles":
        viewingDF = viewingDF[viewingDF["Profile Name"] == selectedProfile] 
    
    viewingDF["Series Name"] = viewingDF["Title"].str.split(":").str[0].apply(clean_title)
    viewingDF["Duration Seconds"] = viewingDF["Duration"].apply(parseDuration)

    return viewingDF.groupby("Series Name")["Duration Seconds"].sum().sort_values(ascending = False).head(top_n)

def mostWatchedMovies(viewingDF, selectedProfile, top_n=5):
 
    viewingDF = filterRealViews(viewingDF)
    viewingDF = viewingDF[~viewingDF["Title"].str.contains("Episode|episodio", na=False)]

    if not selectedProfile == "All Profiles":
        viewingDF = viewingDF[viewingDF["Profile Name"] == selectedProfile] 
    
    viewingDF["Clean Title"] = viewingDF["Title"].apply(clean_title)
    viewingDF["Duration Seconds"] = viewingDF["Duration"].apply(parseDuration)

    return viewingDF.groupby("Clean Title")["Duration Seconds"].sum().sort_values(ascending=False).head(top_n)




if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nProgram terminated.\n")
