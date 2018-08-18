#flaskのライブラリを入れる
from flask import Flask, render_template, request, logging, Response, redirect, flash
from config import CONFIG
import tweepy
import pandas as pd

CONSUMER_KEY = CONFIG["CONSUMER_KEY"]
CONSUMER_SECRET = CONFIG["CONSUMER_SECRET"]
ACCESS_TOKEN = CONFIG["ACCESS_TOKEN"]
ACCESS_SECRET = CONFIG["ACCESS_SECRET"]

#認証情報
auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
auth.set_access_token(ACCESS_TOKEN, ACCESS_SECRET)

#Tweepyの認証情報をもとにAPIが利用できるインスタンスを作成
api = tweepy.API(auth)

#flaskを初期化してインスタンスを作成する。このappから各種flaskのメソッドを呼び出すことができるようになる
app=Flask(__name__)

#ツイッターからとるデータを設定
columns = [
   "tweet_id",
   "created_at",
   "text",
   "fav",
   "retweets"
   ]

#ルーティング処理
@app.route('/',methods=["GET","POST"])
#./にアクセスしたときにindex.htmlを呼び出す
def index():
    #HTTPのPOSTリクエストが送られた時
    if request.method =='POST':
        #HTMLから受け取った値を、python上で取得
        user_id = request.form['user_id']
        #et_tweets_df関数で、PandasのDataFrame(df)形式でツイートを取得
        tweets_df = get_tweets_df(user_id)
        #取得したDataFrame形式で取得したツイートを、日時集計するget_grouped_df関数で取得
        grouped_df = get_grouped_df(tweets_df)
        #日時順にツイートを並べるget_sorted_df関数で取得
        sorted_df = get_sorted_df(tweets_df)
        #ユーザーIDを、再度HTMLに反映するには、以下のコードを実行する必要
        return render_template(
            'index.html',
            #ユーザーのプロフィールを取得する関数get_profile関数を呼び出し
            profile=get_profile(user_id),
            tweets_df = tweets_df,
            grouped_df = grouped_df,
            sorted_df = sorted_df
            )
    else:
        return render_template('index.html')

def get_tweets_df(user_id):
    #Pandasのデータフレームオブジェクトを、さきほど指定した列名を指定したリストで作成
    tweets_df = pd.DataFrame(columns=columns)
    #ツイッターAPIを利用して、あるユーザーのツイートを取得
    for tweet in tweepy.Cursor(api.user_timeline,screen_name = user_id, exclude_replies = True).items():
        try:
            #ツイートの内容にRT @が入っていない場合のみ、ツイートを取得
            if not "RT @" in tweet.text:
                #ツイッターのAPIから取得したそれぞれの値を、PandasのSeriesオブジェクト形式で取得
                se = pd.Series([
                    tweet.id,
                    tweet.created_at,
                    tweet.text.replace('\in',''),
                    tweet.favorite_count,
                    tweet.retweet_count

                    ]
                    ,columns
                    )
                #
                tweets_df = tweets_df.append(se, ignore_index=True)
        
        except Exception as e:
            print(e)
    #のちほど日別でデータの処理ができるように、作成日のデータをdatetime型に変換
    tweets_df["created_at"] = pd.to_datetime(tweets_df["created_at"])
    return tweets_df

def get_profile(user_id):
    #ユーザーidを指定して、ユーザーの情報を取得
    user = api.get_user(screen_name = user_id)
    #それぞれプロフィールで必要な値を取得
    profile = {
        "id": user.id,
        "user_id": user_id,
        "image": user.profile_image_url,
        "description": user.description
    }
    return profile

def get_grouped_df(tweets_df):
    #日付で集計し、それらの値をsum関数で合計し、sort_values関数でcreated_at中に並べる
    grouped_df = tweets_df.groupby(tweets_df.created_at.dt.date).sum().sort_values(by="created_at",ascending=False)
    return grouped_df

def get_sorted_df(tweets_df):
    #tweets_dfをretweets順に並び替えて、降順にしたものを返す
    sorted_df = tweets_df.sort_values(by="retweets",ascending="False")
    return sorted_df

if __name__ == '__main__':

    app.run(host="localhost")
