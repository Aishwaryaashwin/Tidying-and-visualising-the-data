from flask import Flask, render_template, request, session, redirect

import more_itertools

import altair as alt
import pandas as pd


alt.data_transformers.disable_max_rows()


app = Flask(__name__)
data_clean = pd.read_csv("data/tidy_data.csv")

data_clean["Connection_Num"] = data_clean["Connection_Num"].astype('int')
symbols = sorted(data_clean['Councils'].unique())
SortedYears = sorted(data_clean['Year'].unique())

def produce_table(symbols, size=10):
    output = "<table>"
    for chunk in more_itertools.chunked(symbols, size):
        # chunk is the next 10 symbols
        output += "<tr>"
        for s in chunk:
           output += f"<td><input type='checkbox' name='{s}' value='{s}'>{s}</td>"
        output += "</tr>"
    output += "</table>"
    return output   

def produce_year_table(SortedYears, size=10):
    output = "<table>"
    for chunk in more_itertools.chunked(SortedYears, size):
        # chunk is the next 10 symbols
        output += "<tr>"
        for s in chunk:
           output += f"<td><input type='checkbox' name='{s}' value='{s}'>{s}</td>"
        output += "</tr>"
    output += "</table>"
    return output  

@app.route("/")
@app.route("/symbols")
def show_symbols():
    the_table = produce_table(symbols, 6)
    return render_template("checks.html", data=the_table)
    
@app.route("/processchecks", methods=["POST"])
def process_checks():
    print('*'*60)
    print(request.form)  # This gets at the FORM data.
    print(list(request.form.keys()))
    session["selection"] = list(request.form.keys())
    print('*'*60)
    return redirect("/Years")

@app.route("/Years")
def show_years():
    year_table = produce_year_table(SortedYears, 6)
    return render_template("checks_years.html", data=year_table)

@app.route("/processchecksYears", methods=["POST"])
def process_years_checks():
    print('*'*60)
    print(list(request.form.keys()))
    session["Years_Selection"] = list(request.form.keys())
    print('*'*60)
    return redirect("/visual")
    
@app.route("/visual")
def display_the_plot():
    df = pd.concat(
        data_clean[data_clean['Councils'] == stock] for stock in session["selection"]
    )
    filtered_df = pd.concat(
        df[df['Year'] == int(year)] for year in session["Years_Selection"]
    )
    print(filtered_df.head())
    plot1 = alt.Chart(df,title='Trend on the total number of connections for selected councils from 2006 to 2013 (Dynamic based on Councils)').mark_point(size=70,filled=True).encode(
    alt.X(
        "Councils",
        title="Councils"),
    alt.Y(
        'sum(Connection_Num)',
        title="Total ESB connections"
        
    ),
    color='Year:N',
    column='Year',
    tooltip=['Councils', 'sum(Connection_Num)']
    ).properties(
    width = 500,
    height = 500)
    
    tidy_data1=data_clean[data_clean["Councils"].str.contains(pat = '_CityCouncil',regex = True)]
    graph=alt.Chart(tidy_data1,title='Average ESB connections for each city councils (Static Plot)').mark_bar(color='firebrick').encode(
          alt.X('average(Connection_Num):Q',
          title="Average ESB Connections"),
          alt.Y('Councils:N', sort='-x',
          title="City Councils")
            )
    text = graph.mark_text(align='left',baseline='middle',color="blue",angle=0).encode(
    text='average(Connection_Num)'
    )
    plot2 =graph+text
    sample1=filtered_df.query("Month in ['Jan','Feb','Mar']")
    sample2=filtered_df.query("Month in ['Apr','May','Jun']")
    sample3=filtered_df.query("Month in ['Jul','Aug','Sep']")
    sample4=filtered_df.query("Month in ['Oct','Nov','Dec']")
    sample_1=alt.Chart(sample1,width=150).mark_area().encode(
         alt.X(
            "Month", sort = ['Jan','Feb','Mar'],
            title="First Quarter"),
        alt.Y(
            'sum(Connection_Num)',
            title="ESB connections for first quarter"),
            color='Year:N',
            tooltip=['Month', 'Year','sum(Connection_Num)']
            )
    sample_2=alt.Chart(sample2,width=150, title='ESB Connections on Quarterly basis for selected years ').mark_area().encode(
         alt.X(
            "Month",sort = ['Apr','May','Jun'],
            title="Second Quarter"),
        alt.Y(
            'sum(Connection_Num)',
            title="ESB connections for Second quarter"),
            color='Year:N',
            tooltip=['Month', 'Year','sum(Connection_Num)']
            )
    sample_3=alt.Chart(sample3,width=150,title='(Dynamic based on Year)').mark_area().encode(
         alt.X(
            "Month",sort = ['Jul','Aug','Sep'],
            title="Third Quarter"),
        alt.Y(
            'sum(Connection_Num)',
            title="ESB connections for Third quarter"),
        color='Year:N',
            tooltip=['Month', "Year",'sum(Connection_Num)']
            )
    sample_4=alt.Chart(sample4,width=150).mark_area().encode(
         alt.X(
            "Month",sort = ['Oct','Nov','Dec'],
            title="Fourth Quarter"),
        alt.Y(
            'sum(Connection_Num)',
            title="ESB connections for fourth quarter"),
        color='Year:N',
            tooltip=['Month', 'Year','sum(Connection_Num)']
            )   
    plot3 = sample_1|sample_2|sample_3|sample_4
    
    appended_data = []
    for r in session["Years_Selection"]:
        All_Councils= filtered_df[filtered_df["Year"]==int(r)].groupby(['Councils','Year']).sum().sort_values(by='Connection_Num',ascending=False)
        appended_data.append(All_Councils)
    appended_data = pd.concat(appended_data)
    appended_data=appended_data.reset_index()
    appended_data["Year"]=appended_data["Year"].astype(str)
    
    Bar=alt.Chart().mark_bar(opacity=0.8,color="steelblue",size=3.25).encode(
            x= alt.X(
            'Year',
            title=" Years from 2006 to 2013"),
            y=alt.Y(
            'Connection_Num',
        )).properties(
    width = 200,
    height = 250)
    Name=Bar.mark_text(align='left',baseline='bottom',angle=325,size=11.5).encode(
        text ='Connection_Num')

    line = alt.Chart().mark_line(color="red",size=1.5).encode(
            x= alt.X(
            "Year"),
            y=alt.Y(
            'Connection_Num',
                title='Total ESB Connections',
            )
        ).properties(
    width = 200,
    height = 250)
    plot4=alt.layer(Bar,Name,line).facet("Councils:N", data=appended_data,title='Total Number of connections for selected year and Councils (Dynamic based on Council and Year)')
    
    plot5 = alt.Chart(filtered_df,title='Max & Min number of connections for all the months in the selected Years (Dynamic based on the Year)').mark_boxplot(extent='min-max',size=25).encode(
         alt.X(
            "Month:O", sort = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'],
            title="Month"),
        alt.Y(
            'Connection_Num:Q',
            title="Total ESB connections"),
          color='Year:N'
        ).properties(
    width = 500,
    height = 500)
    
    plot=alt.vconcat(plot3,plot4,plot5,plot1,plot2, spacing =50)
    plot.save("templates/plots.html")
    return render_template("plots.html")  


   
app.secret_key = ".v/vndfl/n/dlfkn/ldfkn/ldkngLKN"


if __name__ == "__main__":
    app.run(debug=True)






