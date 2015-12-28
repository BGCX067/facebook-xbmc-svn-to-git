import urllib,urllib2,re,xbmcplugin,xbmcgui,os,datetime
from fbapi import Facebook,FacebookError

#.nF0
__plugin__  = "Facebook News Feed"
__author__  = "leo212"
__date__    = "6 10 2009"
__version__ = "1"

dialog = xbmcgui.Dialog()
pDialog = xbmcgui.DialogProgress()
pDialog.create( sys.modules[ "__main__" ].__plugin__ )

settings = {}
fb = {}

YOUTUBE_URL_FORMAT = "http://www.youtube.com/v/(.*)&"
YOUTUBE_WATCH_URL = "http://www.youtube.com/watch?v=%s"
YOUTUBE_SIG_REGEXP = 'var swfArgs = {.*"t": "(.*?)".*}'
YOUTUBE_DIRECT_VIDEO_PLAY = 'http://www.youtube.com/get_video?fmt=18&video_id=%s&t=%s'

# settings enum
API_KEY, SECRET_KEY, SESSION_KEY, UID, USERNAME, PASSWORD = range(6)
def get_settings():        
        settings[API_KEY] =  xbmcplugin.getSetting( "api_key" )
        settings[SECRET_KEY] =  xbmcplugin.getSetting( "secret_key" )
        settings[SESSION_KEY] =  xbmcplugin.getSetting( "session_key" )
        settings[UID] =  xbmcplugin.getSetting( "uid" )
        settings[USERNAME] =  xbmcplugin.getSetting( "username" )
        settings[PASSWORD] =  xbmcplugin.getSetting( "password" )

def save_settings():
        xbmcplugin.setSetting( "session_key", settings[SESSION_KEY] )
        xbmcplugin.setSetting( "uid", settings[UID] )

def facebook_login():
        try:     
                pDialog.update( 0, xbmc.getLocalizedString( 30016 ))
                fb.auth.createToken()
                pDialog.update( 10, xbmc.getLocalizedString( 30017 ))
                fb.login(settings[USERNAME],settings[PASSWORD])
                pDialog.update( 80, xbmc.getLocalizedString( 30018 ))
                session = fb.auth.getSession()
                settings[SESSION_KEY] = session["session_key"]
                settings[UID] = session["uid"]
                pDialog.update( 80, xbmc.getLocalizedString( 30019 ))
                save_settings()
        except FacebookError, (err):                        
                dialog.ok(xbmc.getLocalizedString( 30000 ), (xbmc.getLocalizedString( 30012 ) % err.code), err.msg)                

def facebook_login_with_session():
        try:     
                pDialog.update( 80, xbmc.getLocalizedString( 30020))        
                fb.session_key = settings[SESSION_KEY]
                fb.uid =  settings[UID]
                # check if the connection was successfull
                return True
        except FacebookError, (err):
                # if session was expired
                if (err.code == "102"):
                        return False
                else:
                        dialog.ok(xbmc.getLocalizedString( 30000 ), (xbmc.getLocalizedString( 30012 ) % err.code), err.msg)

def remove_html_tags(data):
    # convert <br>'s to spaces
    data = data.replace("<BR>"," ").replace("<br>"," ")
    # remove html tags
    p = re.compile(r'<.*?>')
    return p.sub('', data)

def show_news_feed():
        pDialog.update( 90, xbmc.getLocalizedString( 30021 ))
        feeds = fb.fql.query("SELECT created_time , post_id, actor_id, target_id, message, attachment FROM stream WHERE source_id in (SELECT target_id FROM connection WHERE source_id='%s' AND is_following=1) AND is_hidden = 0 LIMIT 0,50" % fb.uid)

        pDialog.update( 100, xbmc.getLocalizedString( 30022 ))
        uids = []
        pids = []
        posts_images = {}
        posts_preview = {}
        posts_types = {}
        posts_links = {}
        posts = {}
        
        for feed in feeds:
                # set default type
                feed["genre"] = "Status"
                
                # add user to the list of users to query
                uids.append(feed['actor_id'])
                
                # look for attachments to load 
                attachment = feed['attachment']
                if ((type(attachment) == dict)):                        
                        # store attachment name
                        if (attachment.has_key('name')):
                            feed["attname"] = remove_html_tags(attachment["name"])
                        elif (attachment.has_key('description')):
                            feed["attname"] = remove_html_tags(attachment["description"])                                    

                        # use it as a message, if feed doesn't have a message
                        if (feed["message"]==""):
                            feed["message"]=feed["attname"]
                           
                        # check for media in the attachment
                        if (attachment.has_key('media')):                                
                                media = attachment['media']
                                if (len(media) > 0):
                                        for m in media:                                                
                                                if (m['type']=='photo'):
                                                        pids.append(m['photo']['pid'])
                                                        # store the first photo as the post image
                                                        if (not posts_images.has_key(feed["post_id"])):
                                                                posts_images[feed["post_id"]] = m['photo']['pid']  
                                                        feed["genre"]="Photo"
                                                elif (m['type']=='link'):
                                                        if (not posts_preview.has_key(feed["post_id"])):
                                                                link = m["src"]
                                                                if (link.endswith(".png") or link.endswith(".jpg") or link.endswith(".gif")):
                                                                        posts_preview[feed["post_id"]] = link
                                                                        posts_types[feed["post_id"]] = "picture"
                                                                        posts_links[feed["post_id"]] = link
                                                        feed["genre"]="Link"
                                                elif (m['type']=='image'):
                                                        if (not posts_preview.has_key(feed["post_id"])): 
                                                                posts_preview[feed["post_id"]] = m["src"]
                                                                posts_types[feed["post_id"]] = "picture"
                                                                posts_links[feed["post_id"]] = link
                                                        feed["genre"]="Image"
                                                elif (m['type']=='flash'):
                                                        if (not posts_preview.has_key(feed["post_id"])): 
                                                                if (m.has_key("imgsrc")):
                                                                        posts_preview[feed["post_id"]] = m["imgsrc"]
                                                                        posts_types[feed["post_id"]] = "picture" 
                                                        feed["genre"]="Flash"
                                                elif (m['type']=='video'):
                                                        if (not posts_preview.has_key(feed["post_id"])): 
                                                                if (m.has_key("preview_img")):
                                                                        posts_preview[feed["post_id"]] = m["preview_img"]
                                                                else:
                                                                        posts_preview[feed["post_id"]] = m["src"]
                                                                posts_types[feed["post_id"]] = "video"
                                                                vid = m["video"]
                                                                posts_links[feed["post_id"]] = vid["source_url"]
                                                                feed["genre"]="Video"

        #load all of the photos
        if (len(pids)>0):
                photos = fb.photos.get(pids=pids)
        else:
                photos = []

        #build an photos hashmap
        photos_hashmap = {}
        for photo in photos:
                photos_hashmap[photo["pid"]] = photo["src_big"]

        #load user info data                                                      
        users = fb.users.getInfo(uids, ['uid','name','pic'])
        users_hash = {}
        #build a user hashmap
        for user in users:
                users_hash[user['uid']]=user

		feednum = 1
        for feed in feeds:
                icon="blank.tbn"
                link=""
                if (posts_types.has_key(feed["post_id"])):
                    if (posts_types[feed["post_id"]] == "picture"):
                            icon="DefaultPicture.png"
                    elif (posts_types[feed["post_id"]] == "video"):
                            icon="DefaultVideo.png"
                            if (posts_links.has_key(feed["post_id"])):
                                    link=posts_links[feed["post_id"]]
                # search image 
                image = ""
                if ( posts_images.has_key(feed["post_id"])):                        
                        image = photos_hashmap[posts_images[feed["post_id"]]]
                        link = image
                elif ( posts_preview.has_key(feed["post_id"])):                        
                        image = posts_preview[feed["post_id"]]
                elif (users_hash.has_key(feed['actor_id'])):
                        image = users_hash[feed['actor_id']]['pic']

                #creationDate = datetime.datetime.fromtimestamp(int(feed["created_time"]))
                #creationDateStr = creationDate.strftime("%Y-%m-%d %H:%M")
                if (users_hash.has_key(feed['actor_id'])):
                        username = users_hash[feed['actor_id']]['name']
                        feednumstr = "%0*d" % (2,feednum)
                        title = "%s:[B]%s[/B] %s" % (feednumstr, username, feed["message"].split("\n")[0])
                else:
                        title = "%s:%s" % (feednumstr, feed["message"].split("\n")[0])

                listitem = xbmcgui.ListItem(title, "", icon, image)
                
                if (link == ""):
                        url=feed["post_id"]
                elif re.match(YOUTUBE_URL_FORMAT, link):                        
                        feed["genre"] = "YouTube"
                        code = re.findall(YOUTUBE_URL_FORMAT,link)[0]
                        url="%s?playYouTube&code=%s&title=%s&moviename=%s" % (path, code, title, feed["attname"])
                else:
                        url="%s?playMedia&title=%s&url=%s&moviename=%s" % (path, title, link, feed["attname"])
                        
                creationDate = datetime.datetime.fromtimestamp(int(feed["created_time"]))
                date = creationDate.strftime("%d/%m/%Y")
                listitem.setInfo( type="Video", infoLabels={ "Title": title, "Genre": feed["genre"], "Date":date} )
                xbmcplugin.addDirectoryItem( handle=int( handle ), url=url, listitem=listitem, isFolder=False, totalItems=len(feeds))                
                feednum = feednum + 1
                
def get_youtube_url(code):        
        usock = urllib.urlopen(YOUTUBE_WATCH_URL % code)        
        # read source
        htmlsrc = usock.read()
        
        # close socket
        usock.close()

        # find youtube signature
        sig = re.findall(YOUTUBE_SIG_REGEXP, htmlsrc)
        if (len(sig)>0):                
                url = YOUTUBE_DIRECT_VIDEO_PLAY % (code, sig[0])                
                return url
        else:
                xbmc.log("play_youtube: no data found on youtube page")
        
def read_params(params_str):        
        params = {}
        if (len(params_str.split("?"))==2):
                args=params_str.split("?")[1].split("&")
                for arg in args:
                        pair = arg.split("=")
                        if (len(pair)==2):
                                params[pair[0]]=pair[1]
                        else:
                                params[pair[0]]=True
        return params
            
################ MAIN ####################
# read paramters
path = sys.argv[0]
handle = sys.argv[1]
params_str = sys.argv[2]
params = read_params(params_str)
            
# read settings from settings.xml
get_settings()                                       

if (len(params)==0):
        try:
            fb = Facebook(settings[API_KEY], settings[SECRET_KEY])

            # if there is no facebook session id
            if (settings[SESSION_KEY] == ""):
                    # login for the first time
                    facebook_login()
            else:
                    # try to connect with the session id
                    if (not facebook_login_with_session()):
                            # if doesn't work - login with user & password to get a new session id
                            facebook_login()
            
            show_news_feed()
        except FacebookError, (err):
                if (err.code == "612"):
                        fb.request_extended_permission("read_stream")
                        dialog.ok(xbmc.getLocalizedString( 30000 ), xbmc.getLocalizedString( 30013 ), xbmc.getLocalizedString( 30014 ),xbmc.getLocalizedString( 30015 ))                        
                elif (err.code == "102"):
                        facebook_login()
                        show_news_feed()
                else:
                        raise
else:
        if params.has_key("playMedia"):
                listitem = xbmcgui.ListItem(params["moviename"])
                pDialog.update( 100, xbmc.getLocalizedString( 30023 ) % params["moviename"])
                xbmc.Player().play( params["url"], listitem )
        elif params.has_key("playYouTube"):
                pDialog.update( 0, xbmc.getLocalizedString( 30024 ))                
                url = get_youtube_url(params["code"])
                listitem = xbmcgui.ListItem(params["moviename"])
                pDialog.update( 100, xbmc.getLocalizedString( 30023 ) % params["moviename"])
                xbmc.Player().play( url, listitem )

xbmcplugin.addSortMethod(int(handle), xbmcplugin.SORT_METHOD_GENRE)           
xbmcplugin.addSortMethod(int(handle), xbmcplugin.SORT_METHOD_DATE)           
xbmcplugin.addSortMethod(int(handle), xbmcplugin.SORT_METHOD_TITLE)           
xbmcplugin.endOfDirectory(int(handle))
pDialog.close()
