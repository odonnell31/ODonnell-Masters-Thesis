# -*- coding: utf-8 -*-
"""
Created on Thu Sep 10 21:34:23 2020

@author: ODsLaptop

@title: spotify API for podcast and music data
"""

#import needeed libraries
import requests
import base64
import datetime
import pandas as pd
from urllib.parse import urlencode
import json


# from https://developer.spotify.com/dashboard/applications/12e3a84c48794da1b01d8c83894b9b22
client_id = '12e3a84c48794da1b01d8c83894b9b22'
client_secret = 'a83d66bf68004a038c4d83eb110e547d'

### Connecting to Spotify ###
# create SpotifyAPI class
class SpotifyAPI(object):
    access_token = None
    access_token_expires = datetime.datetime.now()
    access_token_did_expire = True
    client_id = None
    client_secret = None
    token_url = 'https://accounts.spotify.com/api/token'
    
    def __init__(self, client_id, client_secret, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_id = client_id
        self.client_secret = client_secret
        
    def get_client_credentials(self):
        """
        Returns a base64 encoded string
        """
        client_id = self.client_id
        client_secret = self.client_secret
        
        if client_secret == None or client_id == None:
            raise Exception("you must set client_id and client_secret")
        
        client_creds = f"{client_id}:{client_secret}"
        client_creds_b64 = base64.b64encode(client_creds.encode())
        return client_creds_b64.decode()
        
    def get_token_headers(self):
        client_creds_b64 = self.get_client_credentials()
        
        return {
            'Authorization': f"Basic {client_creds_b64}"
        }
    
    def get_token_data(self):
        return {
            'grant_type': 'client_credentials'
        }
        
    def perform_auth(self):
        token_url = self.token_url
        token_data = self.get_token_data()
        token_headers = self.get_token_headers()
        
        r = requests.post(token_url, data = token_data, headers = token_headers)

        if r.status_code not in range(200,299):
            raise Exception("Could not authenticate client..")
            # return False
        
        data = r.json()
        now = datetime.datetime.now()
        access_token = data['access_token']
        expires_in = data['expires_in'] #seconds
        expires = now + datetime.timedelta(seconds = expires_in)
        self.access_token = access_token
        self.access_token_expires = expires
        self.access_token_did_expire = expires < now
            
        return True
    
    def get_access_token(self):
        token = self.access_token
        expires = self.access_token_expires
        now = datetime.datetime.now()
        if expires < now:
            self.perform_auth()
            return self.get_access_token()
        elif token == None:
            self.perform_auth()
            return self.get_access_token()
        return token
    
    def get_resource_header(self):
        access_token = self.get_access_token()
        headers = {
            'Authorization': f"Bearer {access_token}"
        }
        return headers
    
    def get_resource(self, lookup_id, resource_type = 'shows', version='v1', market = 'US'):
        if resource_type == 'shows':
            endpoint = f"https://api.spotify.com/{version}/shows/{lookup_id}/episodes"
        else:
            endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        #endpoint = f"https://api.spotify.com/{version}/{resource_type}/{lookup_id}"
        headers = self.get_resource_header()
        r = requests.get(endpoint, headers=headers)
        print(lookup)
        if r.status_code not in range(200,299):
            return {}
        return r.json()
    
    
    
    ### Searching Spotify ###
    # search Spotify by name
    def search(self, query, search_type = 'artists', market = 'US'):
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/search"
        data = urlencode({'q': query, 'type': search_type.lower(), 'market': market})
        lookup_url = f"{endpoint}?{data}"
        print(lookup_url)
        r = requests.get(lookup_url, headers = headers)
        if r.status_code not in range(200,299):
            return "somethings wrong"
        return r.json()
    
    
    
    ### Retrieving Music Data ###
    # get album information
    def get_album(self, _id):
        return self.get_resource(_id, resource_type='albums')
    
    # get artist information
    def get_artist(self, _id):
        return self.get_resource(_id, resource_type='artists')
    
    
    
    ### Retrieving Podcast Data ###
    # get episodes information
    #def get_episodes(self, _id):
    #    return self.get_resource(_id, resource_type='shows')
    
    # get the following columns about a podcast:
        #name, publisher, total_episodes, id, media_type,
        #description, external_urls, uri
    def get_podcast_info_by_id(self, showid, market = 'US'):
        headers = self.get_resource_header()
        endpoint = "https://api.spotify.com/v1/shows"
        data = urlencode({'ids': showid, "market": market})
        lookup_url = f"{endpoint}?{data}"
        #print(lookup_url)
        r = requests.get(lookup_url, headers = headers)
        if r.status_code not in range(200,299):
            return "somethings wrong"
        
        raw_json = r.json()
        
        podcast_dict = {'name': raw_json['shows'][0]['name'],
            'publisher': raw_json['shows'][0]['publisher'],
            'total_episodes': raw_json['shows'][0]['total_episodes'],
            'id': raw_json['shows'][0]['id'],
            'media_type': raw_json['shows'][0]['media_type'],
            'description': raw_json['shows'][0]['description'],
            'external_urls': raw_json['shows'][0]['external_urls'],
            'uri': raw_json['shows'][0]['uri']}
        
        return podcast_dict
    
    # get multiple podcasts info in a dataframe
    def multiple_podcasts_info(self, list_of_ids):
        # create empty dataframe
        podcasts_info_df = pd.DataFrame(columns = ['name', 'publisher','total_episodes',
                                                     'id','media_type', 'description',
                                                     'external_urls', 'uri'])
        
        # grab podcast info from each id and append to dataframe
        for i in list_of_ids:
            temp_dict = self.get_podcast_info_by_id(i)
            df = pd.DataFrame(temp_dict, columns = ['name', 'publisher',
                                                  'total_episodes', 'id',
                                                  'media_type', 'description',
                                                  'external_urls', 'uri'])
            #print(df)
            podcasts_info_df = podcasts_info_df.append(df)
            
        podcasts_info_df = podcasts_info_df.reset_index(drop=True)
        
        return podcasts_info_df
    
    # get podcast episodes from a show
    def get_podcast_episodes_by_id(self, showid, num_episodes = 10, market = 'US'):
        headers = self.get_resource_header()
        endpoint = f"https://api.spotify.com/v1/shows/{showid}/episodes?offset=0&limit={num_episodes}&market=US"
        #data = urlencode({'ids': showid, "market": market})
        lookup_url = f"{endpoint}"
        #print(lookup_url)
        r = requests.get(lookup_url, headers = headers)
        if r.status_code not in range(200,299):
            return "somethings wrong"
        
        raw_json = r.json()
    
        episode_df = pd.DataFrame(columns = ['name','release_date','duration_min',
                                     'external_urls','id', 'language',
                                     'release_date_precision', 'uri','description'])

        for i in range(num_episodes):
            # create a dict with the data
            temp_dict = {'name': raw_json['items'][i]['name'],
                       'release_date': raw_json['items'][i]['release_date'],
                       'duration_min': round((raw_json['items'][i]['duration_ms'])/60000,2),
                       'external_urls': raw_json['items'][i]['external_urls'],
                       'id': raw_json['items'][i]['id'],
                       'language': raw_json['items'][i]['language'],
                       'release_date_precision': raw_json['items'][i]['release_date_precision'],
                       'uri': raw_json['items'][i]['uri'],
                       'description': raw_json['items'][i]['description']}

            df = pd.DataFrame(temp_dict, columns = ['name','release_date','duration_min',
                                     'external_urls','id', 'language',
                                     'release_date_precision', 'uri','description'])
            episode_df = episode_df.append(df)

        episode_df = episode_df.reset_index(drop=True)
        return episode_df
    
 
    
    
### Recurring API Calls for Database ###

# instantiate spotifyAPI class object
spotify = SpotifyAPI(client_id, client_secret)
    
# define podcast id's
The_Ryen_Russillo_Podcast_id = '2XdegS23ImVZldex799DUS'
The_Bill_Simmons_Podcast_id = '07SjDmKb9iliEzpNcN2xGD'
Pardon_My_Take_id = '5ss1pqMFqWjkOpt6Ag0fZW'
Against_All_Odds_with_Cousin_Sal_id = '7f6QwdOqt2T3DfDc7zdCYy'

Trail_Runner_Nation = '603z2wAQ73kcqTbM1pTl74'
The_Running_Public = '2vUYerXBNhRDPcaINbYK8I'
Another_Mother_Runner = '7HlsUrk4KVfMrX0dcqkT8e'
The_Running_Pod = '2PacGg6zS1UZzOtS680MrR'
Run_to_the_Top_Podcast = '4sIXIw0CbMW0on5zKXAet1'
The_Strength_Running_Podcast = '1ZkJ0i0utCvF8NidUvfyYW'
Running_Lean = '72KqZFtcRSoZFpPVTgJYvZ'
RunBuzz_Running_Podcast = '43fRWm1WJwVZZ9kGnfIngU'
Running_Things_Considered = '7L5aLeFO5zDMcinUfrm8oV'
The_Runners_Zone = '4qMTmxMVJAKuUk5K7zZz55'
Runners_of_NYC = '4DD2jtIBEcyVohfiimggvM'
The_Runners_World_Show = '5LYUDIwTqW0vogUVpicWto'
Not_Real_Runners = '3ysDuOiqvtPhRav34aMPwW'
Coaching_Runners = '79ibGRJzwgqUyLdOT3IKvL'

# create lists of id's
sports_podcast_ids = [The_Ryen_Russillo_Podcast_id,
                  The_Bill_Simmons_Podcast_id,
                  Pardon_My_Take_id,
                  Against_All_Odds_with_Cousin_Sal_id]

running_podcast_ids = [Trail_Runner_Nation,
                       The_Running_Public,
                       Another_Mother_Runner,
                       The_Running_Pod,
                       Run_to_the_Top_Podcast,
                       The_Strength_Running_Podcast,
                       Running_Lean,
                       RunBuzz_Running_Podcast,
                       Running_Things_Considered,
                       The_Runners_Zone,
                       Runners_of_NYC,
                       The_Runners_World_Show,
                       Not_Real_Runners,
                       Coaching_Runners]
    
### Recurring API Call for Shows' Info ###
def shows_info_spotifyAPI_call(podcast_ids_list):
    multiple_podcasts_df = spotify.multiple_podcasts_info(podcast_ids_list)
    
    ### query to put data into database
    
    return multiple_podcasts_df

### Recurring API Call for Episodes Info ###
def episodes_info_spotifyAPI_call(podcast_ids_list):
    
    for i in podcast_ids_list:
        episodes_df = spotify.get_podcast_episodes_by_id(i, num_episodes = 50,
                                                         market = 'US')
        
        ### query to put into database
        print(episodes_df)
        
    return episodes_df

#running_podcasts_test_df = shows_info_spotifyAPI_call(running_podcast_ids)
