#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import os
import urllib2
import webapp2
import jinja2
from lxml import etree as ET
import datetime
from google.appengine.ext import db
#--------------------------------------------------------------------------------------------  
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), 'templates')),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)



#-------------------------------------------------------------------------------------------- 
#takes a list of strings of datetime and formats to ouput
#    day of week, month-day-year
def convertTime(time24):
        nTime = []
        #for each string of datetime convert to datetime and 
        #    then convert to desired string output
        for time in time24:
            time.text = time.text[:-6]
            time = datetime.datetime.strptime(time.text, "%Y-%m-%dT%H:%M:%S")
            nTime.append(time.strftime("%A, %m-%d-%Y"))
        return nTime
    
    
    
#--------------------------------------------------------------------------------------------
#Set display variables
def displayVariables(html):    
        #*****************************************************************************
        #parese data and set variables for template 
        root = ET.fromstring(html)        
                         
        minTemp = root.xpath(".//temperature[@type='minimum']/value")
        maxTemp = root.xpath(".//temperature[@type='maximum']/value")
        icon = root.xpath(".//icon-link")
        sum = root.xpath(".//weather-conditions/@weather-summary")
        time24 = root.xpath(".//time-layout/start-valid-time")
        ntime = convertTime(time24)
        lat = root.xpath(".//data/location/point/@latitude")
        lon = root.xpath(".//data/location/point/@longitude")       
        #*****************************************************************************        
        
        # set form variables to be passed to template
        form_values = {'minTemp':minTemp, "maxTemp":maxTemp, "icon":icon, "sum":sum, "time24":ntime, "lat":lat, "lon":lon,}
        return form_values 
 
 
        
#--------------------------------------------------------------------------------------------
#display results from lat and lon input            
class MainHandler(webapp2.RequestHandler):

    def get(self):
        #set latitude and longitude from get request
        lat = self.request.get("lat")
        lon = self.request.get("lon")
        
        # if values aren't set redirect to zip code input
        if lat == None or lat == '':
            self.redirect("/zip")
        if lon == None or lon == '':
            self.redirect("/zip")  
        
        z = ZipWeather.all()
        oldLat = z.filter("latitude =", lat).get()
        oldLon = z.filter("longitude =", lon).get()
        html = None
                
        if oldLat and oldLon:
           html = oldLat.xml
        else:
            #*****************************************************************************
            #get data from national weather service
            request = "http://graphical.weather.gov/xml/sample_products/browser_interface/ndfdBrowserClientByDay.php?lat=%s&lon=%s&format=24+hourly&numDays=5" %(str(lat), str(lon))
            response = urllib2.urlopen(request)
            html = response.read()
            new = ZipWeather(latitude=lat, longitude=lon, xml=html)
            new.put()  
            #*****************************************************************************        
        
        # set form variables to be passed to template
        form_values = displayVariables(html)
        
        #display webpage       
        form_template = JINJA_ENVIRONMENT.get_template('view.html')        
        self.response.write(form_template.render(form_values))
        
        
        
#--------------------------------------------------------------------------------------------
#display zip code input page
class ZipHandler(webapp2.RequestHandler):
    def get(self):
        form_template = JINJA_ENVIRONMENT.get_template('zipForm.html')        
        self.response.write(form_template.render())
        
        

#--------------------------------------------------------------------------------------------  

#Data to store zip code searches
class ZipWeather(db.Model):
    zipp = db.StringProperty()
    xml = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    latitude = db.StringProperty()
    longitude = db.StringProperty()

      
#--------------------------------------------------------------------------------------------          
class EmptyHandler(webapp2.RequestHandler):    
    
    def get(self):
        z = ZipWeather.all()        
        db.delete(z.fetch(None))
               
        
      
#--------------------------------------------------------------------------------------------        
class ZipViewHandler(webapp2.RequestHandler):

    def get(self):
        #set variable for request
        zip = self.request.get("zip")
        
        #if not set redirect to zip code input        
        if zip == None or zip == '':
            self.redirect("/zip") 
        
        z = ZipWeather.all()
        old = z.filter("zipp =", zip).get()
        html = None
                
        if old:
           html = old.xml
        else:
            #*****************************************************************************
            #get data from national weather service
            request = "http://graphical.weather.gov/xml/sample_products/browser_interface/ndfdBrowserClientByDay.php?zipCodeList=%s&format=24+hourly&numDays=5" %(str(zip))
            response = urllib2.urlopen(request)
            html = response.read() 
            new = ZipWeather(zipp=zip, xml=html)
            new.put()
            #*****************************************************************************     

       # set form variables to be passed to template
        form_values = displayVariables(html)
        
        #display webpage       
        form_template = JINJA_ENVIRONMENT.get_template('view.html')        
        self.response.write(form_template.render(form_values))   

#--------------------------------------------------------------------------------------------          
app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/zip', ZipHandler),
    ('/zipView', ZipViewHandler),
    ('/empty', EmptyHandler),
    
    
], debug=True)
