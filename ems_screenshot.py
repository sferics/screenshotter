# Description: Takes screenshot(s) of the DWD or UWZ warning maps or metmaps.eu
__version__ = "1.3.3"
__author__  = "Juri Hubrig"


# import necessary modules
import sys
import logging
import argparse
import traceback
import configparser
from pathlib import Path, PurePath
from multiprocessing import Process
from time import sleep
from datetime import datetime as dt, timedelta as td, timezone as tz


# define the available browsers
browsers_available = {"chromium", "chrome", "firefox", "edge", "webkit"}


def u(args, dt_utc, logger):
   """
   Takes a screenshot of the UWZ weather warning map for Germany.
   """
   # set the URL and image path
   URL         = 'https://www.weatherpro.com/de/germany/berlin/berlin/iframe?mapregion=deutschland'
   image_path  = Path(f"{args.output_dir}/uwz_{dt_minutes_file(dt_utc)}.png")

   # use playwright to take a screenshot of the UWZ weather warning map
   with sync_playwright() as p:
      
      # open the chosen browser
      match args.browser:
         case "chromium":
            browser  = p.chromium.launch()
         case "chrome":
            browser  = p.chromium.launch(channel="chrome")
         case "firefox":
            browser = p.firefox.launch()
         case "edge":
            browser = p.chromium.launch(channel="msedge")
         case "webkit":
            browser = p.webkit.launch()
         case _:
            err = f"Browser {args.browser} not supported. Please choose from {browsers_available}."
            if verbose: print(err)
            logger.error(err)
            return

      # create a new browser context with the given user agent and credentials
      context  = browser.new_context(user_agent=args.user_agent)
      page     = context.new_page()
      # set the default timeout for the context and page
      context.set_default_timeout(args.timeout)
      page.set_default_timeout(args.timeout)
      # set the viewport size, only needed when using iframe method
      #page.set_viewport_size({"width": 556, "height": 600})
      try:
         page.goto(URL)
         page.wait_for_load_state("load")
      except Exception as e:
         if args.verbose:
            print(e)
            traceback.print_exc()
         if args.log:
            dtime = utcnow_seconds_str()
            err   = f"{e.__class__.__name__}: {e}"
            trace = traceback.format_exc()
            logger.error(f"{dtime}\n{err}\n{trace}{'-'*114}")
         browser.close(reason=str(e))
         return
      
      # click on cookie banner "ACCEPT", not necessary if we only use the iframe of weatherpro.com
      """
      try:
         page.get_by_role('button', name="ZUSTIMMEN").click()
      except: pass
      """
      
      # wait for map to be fully loaded
      try:
         locator = page.locator('#mapContainer').locator('.leaflet-map-pane').locator('.leaflet-overlay-pane').locator('.leaflet-zoom-animated').locator('g')
         locator.wait_for()
         # if network_idle is True, wait for the network to be idle
         if args.network_idle:
            page.wait_for_load_state('networkidle')
         # else just wait for the correct load state
         else:
            page.wait_for_load_state('load')
      # if an error occurs, handle it
      except Exception as e:
         if args.verbose:
            print(e)
            traceback.print_exc()
         if args.log:
            dtime = utcnow_seconds_str()
            err   = f"{e.__class__.__name__}: {e}"
            trace = traceback.format_exc()
            logger.error(f"{dtime}\n{err}\n{trace}{'-'*114}")
         browser.close(reason=str(e))
         return
      
      # take a screenshot of the UWZ weather warning map
      page.screenshot(
         path = image_path,
         clip = {
            "x":        0,
            "y":        0,
            "width":    556,
            "height":   600
         }
      )
      # close the browser
      browser.close()
   
   # add watermark to the image
   if args.watermark: add_watermark(image_path, "bl", dt_utc)
   

def d(args, dt_utc, logger):
   """
   Takes a screenshot of the DWD weather warning map for Germany.
   """
   # set the URL and image path
   URL         = 'https://www.dwd.de/DE/wetter/warnungen_landkreise/warnWetter_node.html'
   image_path  =  Path(f"{args.output_dir}/dwd_{dt_minutes_file(dt_utc)}.png")
   
   # use playwright to take a screenshot of the DWD weather warning map
   with sync_playwright() as p:
      
      # open the chosen browser
      match args.browser:
         case "chromium":
            browser  = p.chromium.launch()
         case "chrome":
            browser  = p.chromium.launch(channel="chrome")
         case "firefox":
            browser = p.firefox.launch()
         case "edge":
            browser = p.chromium.launch(channel="msedge")
         case "webkit":
            browser = p.webkit.launch()
         case _:
            err = f"Browser {args.browser} not supported. Please choose from {browsers_available}."
            if verbose: print(err)
            logger.error(err)
            return

      # create a new browser context with the given user agent and credentials
      context  = browser.new_context(user_agent=args.user_agent)
      page     = context.new_page()
      # set the default timeout for the context and page
      context.set_default_timeout(args.timeout)
      page.set_default_timeout(args.timeout)
        
      # try to go to the URL
      try:
         page.goto(URL)
      # if an error occurs, handle it
      except Exception as e:
         if args.verbose:
            print(e)
            traceback.print_exc()
         if args.log:
            dtime = utcnow_seconds_str()
            err   = f"{e.__class__.__name__}: {e}"
            trace = traceback.format_exc()
            logger.error(f"{dtime}\n{err}\n{trace}{'-'*114}")
         browser.close(reason=str(e))
         return
      
      # wait for the map to be fully loaded
      try:
         page.wait_for_selector('#appBox') 
         page.wait_for_selector('#headerBox')
         page.wait_for_selector('#svgBox')
         # if network_idle is True, wait for the network to be idle
         if args.network_idle:
            page.wait_for_load_state('networkidle')
         # else just wait for the correct load state
         else:                                                                                                  page.wait_for_load_state('load')
      # if an error occurs, handle it
      except Exception as e:
         if args.verbose:
            print(e)
            traceback.print_exc()
         if args.log:
            dtime = utcnow_seconds_str()
            err   = f"{e.__class__.__name__}: {e}"
            trace = traceback.format_exc()
            logger.error(f"{dtime}\n{err}\n{trace}{'-'*114}")
         browser.close(reason=str(e))
         return
      
      # get the bounding boxes of the elements
      app_box           = page.locator('#appBox').bounding_box()
      header_box        = page.locator('#headerBox').bounding_box()
      svg_box           = page.locator('#svgBox').bounding_box()
      
      # take a screenshot of the DWD weather warning map
      page.screenshot(
         path = image_path,
         clip = {       
            "x":        svg_box['x'],
            "y":        svg_box['y'] - header_box['height'],
            "width":    app_box['width'],
            "height":   svg_box['height'] + header_box['height']
         }
      )
      # close the browser
      browser.close()
   
   # add watermark to the image
   if args.watermark: add_watermark(image_path, "br", dt_utc)


def m(args, dt_utc, logger):
   """
   Takes a screenshot of the MetMaps page using the given URL.
   """
   # set the image path
   image_path = Path(f"{args.output_dir}/metmaps_{dt_minutes_file(dt_utc)}.png")
   
   # use playwright to take a screenshot of the MetMaps page
   with sync_playwright() as p:  
      # open the chosen browser
      match args.browser:
         case "chromium":
            browser  = p.chromium.launch()
         case "chrome":
            browser  = p.chromium.launch(channel="chrome")
         case "firefox":
            browser = p.firefox.launch()
         case "edge":
            browser = p.chromium.launch(channel="msedge")
         case "webkit":
            browser = p.webkit.launch()
         case _:
            err = f"Browser {args.browser} not supported. Please choose from {browsers_available}."
            if verbose: print(err)
            logger.error(err)
            return 
      # create a new browser context with the given user agent and credentials
      context  = browser.new_context(
         user_agent = args.user_agent,
         http_credentials  = {"username": args.username, "password": args.password}
      )
      # create a new page
      page     = context.new_page()
      # set the default timeout for the context and page
      context.set_default_timeout(args.timeout)
      page.set_default_timeout(args.timeout)
      
      # try to go to the URL
      try:
         page.goto(args.URL)
         # if network_idle is True, wait for the network to be idle
         if args.network_idle:
            page.wait_for_load_state('networkidle')
         # else just wait for the correct load state
         else:                                                                                                  page.wait_for_load_state('load')
      # if an error occurs, handle it
      except Exception as e:
         if args.verbose:
            print(e)
            traceback.print_exc()
         if args.log:
            dtime = utcnow_seconds_str()
            err   = f"{e.__class__.__name__}: {e}"
            trace = traceback.format_exc()
            logger.error(f"{dtime}\n{err}\n{trace}{'-'*114}")
         browser.close(reason=str(e))
         return
      
      #TODO fixme or delete
      """
      inputimage = page.locator('form.mf').locator('table').nth(2).locator('tbody')\
         .locator('tr').nth(3).locator('span#container').locator('div#imgdiv')\
         .locator('span#outline').locator('input#inputimage')
      inputimage.wait_for() 
      """
      # try to get the bounding box of the image
      try:
         inputimage = page.locator('#inputimage').bounding_box()
      # if an error occurs, handle it
      except Exception as e:
         if args.verbose:
            print(e)
            traceback.print_exc()
         if log:
            dtime = utcnow_seconds_str()
            err   = f"{e.__class__.__name__}: {e}"
            trace = traceback.format_exc()
            logger.error(f"{dtime}\n{err}\n{trace}{'-'*114}")
         browser.close(reason=str(e))
         return
      
      # take a screenshot of the image
      page.screenshot(
         path = image_path,
         clip = {       
            "x":        inputimage['x'],
            "y":        inputimage['y'],
            "width":    inputimage['width'],
            "height":   inputimage['height']
         }
      )
      # close the browser
      browser.close()
   
   # add watermark to the image
   if args.watermark: add_watermark(image_path, "br", dt_utc)


# get names of all user defined functions https://stackoverflow.com/a/60894911/12935487
all_sites = [f.__name__ for f in globals().values() if type(f) == type(lambda *args: None)]
from playwright.sync_api import sync_playwright
   

def add_watermark(image_path, position, dt_utc):
   """ 
   Adds a datetime watermark to the image.
   """
   from PIL import Image, ImageFont, ImageDraw
   
   # open the image
   image             = Image.open(image_path)
   watermark_image   = image.copy()
   draw              = ImageDraw.Draw(watermark_image)
   
   # get the size of the image 
   w, h = image.size
   # set the position of the watermark  
   if position == "bl":
      # bottom left
      x, y = int(w / 4), int(h - h / 50)
      # set the font size, depending on the height of the image
      font_size = int(h/18)
   elif position == "br":
      # bottom right 
      x, y = int(w - w / 5), int(h - h / 50)
      # set the font size, depending on the width of the image
      font_size = int(w/20)
   
   #font = ImageFont.truetype("arial.ttf", int(font_size/12))
   font = ImageFont.load_default(size=font_size)
   # add watermark
   draw.text((x, y), dt_minutes_mark(dt_utc), fill="red", font=font, anchor='ms')
   # save the image with the watermark
   watermark_image.save(image_path)


# datetime functions for easier handling
#utcnow_minutes       = lambda : dt.utcnow().replace(second=0, microsecond=0)
#utcnow_seconds       = lambda : dt.utcnow().replace(microsecond=0)
utcnow_minutes       = lambda : dt.now(tz.utc).replace(second=0, microsecond=0)
utcnow_seconds       = lambda : dt.now(tz.utc).replace(microsecond=0)

utcnow_minutes_str   = lambda : utcnow_minutes().strftime("%Y-%m-%d %H:%M")
utcnow_seconds_str   = lambda : utcnow_seconds().strftime("%Y-%m-%d %H:%M:%S")
utcnow_metmaps_str   = lambda : utcnow_seconds().strftime("%Y%m%d%H%M")

dt_minutes        = lambda dt_utc : dt_utc.replace(second=0, microsecond=0)
dt_minutes_file   = lambda dt_utc : dt_utc.strftime("%Y-%m-%d_%H%M")
dt_minutes_mark   = lambda dt_utc : dt_utc.strftime("%Y-%m-%d %H:%M")


def clear_output():
   """
   Clears the output in the terminal.
   """
   import os
   os.system('cls' if os.name == 'nt' else "printf '\033c'")


if __name__ == '__main__':

   # read the config file
   config = configparser.ConfigParser(interpolation=None)
   config.read('config.ini')
   
   # facilitate access to general config
   cf_general        = config["general"]
   # get general config settings
   cf_start_datetime = cf_general["start_datetime"]
   cf_end_datetime   = cf_general["end_datetime"]
   cf_output_dir     = cf_general["output_dir"]
   cf_interval       = cf_general["interval"]
   cf_sites          = cf_general["sites"]
   cf_watermark      = cf_general["watermark"]
   cf_user_agent     = cf_general["user_agent"]
   cf_log            = cf_general["log"]
   cf_verbose        = cf_general["verbose"]
   cf_join           = cf_general["join"]
   cf_browser        = cf_general["browser"]
   cf_timeout        = cf_general["timeout"]
   cf_network_idle   = cf_general["network_idle"]

   # same with metmaps-specific config
   cf_metmaps  = config["metmaps"]
   # get metmaps-specific config settings
   cf_username = cf_metmaps["username"]
   cf_password = cf_metmaps["password"]
   cf_URL      = cf_metmaps["URL"]
   # if no URL is given, use the default URL 
   if cf_URL == "": cf_URL = "https://metmaps.eu/"
    
   
   # now parse command line arguments which overwrite the default config settings
   parser = argparse.ArgumentParser(
      # program name and description
      prog        = "EMS Screenshot Tool",
      description = "Takes a screenshot from the DWD or UWZ warning maps or metmaps.eu",
      epilog      = f"© 2025 {__author__}, Version {__version__}"
   )
   
   # add command line arguments
   parser.add_argument('start_end', nargs="*", default=[cf_start_datetime, cf_end_datetime], help="Start/end datetimes or date (format: YYYYMMDDhhmm OR hhmm). Can also be 'now' to start on the next full minute or 'max' (only second argument). If both arguments are 'now' (or no argument given with default config): take screenshot(s) immediatly.")
   parser.add_argument('-s', '--sites', default=cf_sites, help="Choose sites to screenshot ([a]ll, [u]wz, [d]wd, [m]etmaps)")
   parser.add_argument('-i', '--interval', default=cf_interval, type=int, help="Recording interval in minutes")
   parser.add_argument('-o', '--output_dir', default=cf_output_dir, help="Output directory for the screenshots")
   parser.add_argument('-u', '--username', default=cf_username, help="Login username, if needed for site")
   parser.add_argument('-p', '--password', default=cf_password, help="Login password, if needed for site")
   parser.add_argument('-a', '--user_agent', default=cf_user_agent, help="Define a custom user agent, to pretend we are using a different browser")
   parser.add_argument('-U', '--URL', default=cf_URL, help="custom URL for MetMaps")
   parser.add_argument('-w', '--watermark', action='store_true', default=cf_watermark, help="Add datetime watermark")
   parser.add_argument('-l', '--log', action='store_true', default=cf_log, help="Enable logging")
   parser.add_argument('-v', '--verbose', action='store_true', default=cf_verbose, help="Print verbose output")
   parser.add_argument('-j', '--join', action='store_true', help="Join the processes")
   parser.add_argument('-b', '--browser', default=cf_browser, choices=browsers_available, help="Choose the headless browser (e.g. chromium, firefox or other supported/installed browser)")
   parser.add_argument('-t', '--timeout', default=cf_timeout, type=int, help="Timeout for the browser in seconds")
   parser.add_argument('--network_idle', action='store_true', default=cf_network_idle, help="Wait for network idle state before taking screenshot (default: False)")
   
   # parse command line arguments
   args     = parser.parse_args()
   # set verbose variable to the value of the command line argument
   verbose  = args.verbose

   # if verbose print execution time and command line arguments
   if verbose:
      print(f"Execution time: {utcnow_seconds_str()}")
      print("Command line arguments:")
      for arg in vars(args):
         print(f"{arg}: {getattr(args, arg)}")
   
   args.timeout *= 1000  # convert seconds to milliseconds for playwright

   # if the URL contains a datetime, replace it with the current datetime
   # replace a tim=YYYYmmddHHMM with the current datetime using regex
   if "tim=" in cf_URL:
      # import regex module
      import re
      # substitute the datetime in the URL with the current datetime
      cf_URL = re.sub(r'tim=\d{12}', f'tim={utcnow_metmaps_str()}', cf_URL)
      # if verbose: print(cf_URL)
      if verbose:
         print(f"Replaced 'tim=YYYYmmddHHMM' with 'tim={utcnow_metmaps_str()}' in the URL")
   
   # if logging is turned off: log error messages
   if args.log:
      log         = True
      log_level   = logging.ERROR
   # else only log critical (effectively nothing)
   else:
      log_level   = logging.CRITICAL
      log         = False
   
   # create logger
   logger = logging.getLogger(__name__)
   # configure the error log
   logging.basicConfig(filename='error.log', level=log_level)
   
   # if all sites are desired, take all sites, else only the ones specified
   if args.sites == 'a':
      sites = all_sites[:]
   else:
      # check if all sites are in the list of all sites
      sites = [ i for i in all_sites if i in args.sites ]
   
   # create output directory if not existing yet
   Path(args.output_dir).mkdir(parents=True, exist_ok=True)

   
   def get_screenshots(join=True):
      """
      Takes screenshots of the desired sites.
      """
      errors = {}

      # take screenshots for each desired website
      for site in sites:
         # get the function for the desired site
         site_function = globals()[site]
         # get the current datetime in UTC timezone
         #dt_utc = dt.utcnow()
         dt_utc = dt.now(tz.utc)
         # create a new process for each site with the given arguments
         p = Process(
               target=site_function,
               args=(args, dt_utc, logger)
            )
         try:
            # start the process in the background
            p.start()
            # if join is True, wait for the process to finish
            if join: p.join()
         except Exception as e:
            errors[site] = e
            if verbose:
               print(e)
               traceback.print_exc()
            if log:
               dtime = utcnow_seconds_str()
               err   = f"{e.__class__.__name__}: {e}"
               trace = traceback.format_exc()
               logger.error(f"{dtime}\n{err}\n{trace}{'-'*114}")
            # if we have an error, we want to close the process and continue with the next site (if any)
            try:
               # if the process is still running, close it
               p.close()
            except Exception as e:
               errors[site] = e
               if verbose:
                  print(e)
                  traceback.print_exc()
               if log:
                  dtime = utcnow_seconds_str()
                  err   = f"{e.__class__.__name__}: {e}"
                  trace = traceback.format_exc()
                  logger.error(f"{dtime}\n{err}\n{trace}{'-'*114}")
               # if we can't terminate the process, we want to terminate it
               try:
                  p.terminate()
               except Exception as e:
                  errors[site] = e
                  if verbose:
                     print(e)
                     traceback.print_exc()
                  if log:
                     dtime = utcnow_seconds_str()
                     err   = f"{e.__class__.__name__}: {e}"
                     trace = traceback.format_exc()
                     logger.error(f"{dtime}\n{err}\n{trace}{'-'*114}")
                  # as a last resort, we want to kill the process
                  # not using try/finally here, because it should never fail
                  p.kill()
               # to make sure we continue with the next site, we use finally
               # see https://stackoverflow.com/questions/11551996/why-do-we-need-the-finally-clause-in-python
               finally: continue
            finally: continue
         finally: continue
     
      # if we had errors, return them else the empty dict
      return errors
   

   # if 2 command line arguments are present, take them as start and end datetimes
   if len(args.start_end) == 2: 
      start_datetime, end_datetime = args.start_end
   # if only 1 or no command line arguments are present, take the start and end datetimes from the config
   elif len(args.start_end) == 1:
      # if only 1 command line argument is given, take it as start_datetime
      # and set end_datetime to the default end_datetime from the config
      start_datetime, end_datetime = args.start_end[0], cfg.end_datetime
   else: sys.exit("Please enter 1, 2 or NO command line argument(s)")
   
   
   # check if start_datetime is 'now' or a valid datetime
   if start_datetime == "now":
      # get difference from now to the next full minute, so we know how much time we have to run the script
      #dt_now         = dt.utcnow()
      dt_now         = dt.now(tz.utc)
      dt_next_minute = utcnow_minutes() + td(minutes=1)
      buffer_time    = 0

      # if we have less than 1 second left, we need to start 1 minute later, at the next full minute
      # this is necessary so we can make screenshots every minute, as early as possible
      # it should be a very rare case, but better save than sorry, so we try to cover it
      # even if the scripts runs very slowly, 1 second from here to the while loop should be enough
      # if not, we add 1 second to the buffer time
      if (dt_next_minute - dt_now).total_seconds() < 1:
         buffer_time += 1
      
      # add the extra minute + buffer time to the current time
      start_datetime = utcnow_minutes() + td(minutes = 1+buffer_time )
   
   elif len(start_datetime) == 4:
      # if only HHMM is given, take the current date and time
      #dt_now         = dt.utcnow()
      dt_now         = dt.now(tz.utc)
      HHMM           = start_datetime
      start_datetime = dt(dt_now.year, dt_now.month, dt_now.day, int(HHMM[0:2]), int(HHMM[2:]))
   elif len(start_datetime) == 12:
      # if YYYYmmddHHMM is given, take the given date and time
      YYYY           = start_datetime[0:4]
      mmdd           = start_datetime[4:8]
      HHMM           = start_datetime[8:]
      start_datetime = dt(int(YYYY), int(mmdd[0:2]), int(mmdd[2:]), int(HHMM[0:2]), int(HHMM[2:]))
   # if the input is not valid, exit the script
   else: sys.exit("WRONG INPUT: start_datetime has to be 4 or 12 characters long!")
   
   # if the start_datetime is in the past, exit the script
   #if start_datetime < dt.utcnow():
   if start_datetime < dt.now(tz.utc):
      sys.exit("WRONG INPUT: start_datetime needs to be NOW or in the future!")
   

   # check if end_datetime is 'max' or a valid datetime
   if end_datetime == "max":
      # if end_datetime is 'max', set it to the maximum possible datetime
      from datetime import MAXYEAR
      end_datetime = dt(MAXYEAR, 12, 31, 23, 59)
   # if end_datetime is 'now', take a screenshot immediately and exit the script
   elif len(end_datetime) == 4:
      # if only HHMM is given, take the current date and time
      #dt_now         = dt.utcnow()
      dt_now         = dt.now(tz.utc)
      HHMM           = end_datetime
      end_datetime   = dt(dt_now.year, dt_now.month, dt_now.day, int(HHMM[0:2]), int(HHMM[2:]))
   elif len(end_datetime) == 12:
      # if YYYYmmddHHMM is given, take the given date and time
      YYYY           = end_datetime[0:4]
      mmdd           = end_datetime[4:8]
      HHMM           = end_datetime[8:]
      end_datetime   = dt(int(YYYY), int(mmdd[0:2]), int(mmdd[2:]), int(HHMM[0:2]), int(HHMM[2:]))
   elif end_datetime == "now":
      # if end_datetime is 'now', take a screenshot immediately and exit the script
      if verbose: print("Taking screenshot(s) NOW...")
      errors = get_screenshots(join=args.join)
      if errors:
         for e in errors:
             print(f"Error while taking screenshot(s) for {e}: {errors[e]}")
      sys.exit()
   # if the input is not valid, exit the script
   else: sys.exit("WRONG INPUT: end_datetime has to be 4 or 12 characters long!")
   
   # if the end_datetime is in the past, exit the script
   #if end_datetime <= dt.utcnow():
   if end_datetime <= dt.now(tz.utc):
      sys.exit("WRONG INPUT: end_datetime needs to be in the future!")
   

   # wait for start time to begin
   #while dt.utcnow() < start_datetime:
   while dt.now(tz.utc) < start_datetime:
      # if verbose is True, print the remaining time
      if verbose:
         # get the remaining time until the start_datetime
         #remaining_time = start_datetime - dt.utcnow()
         remaining_time = start_datetime - dt.now(tz.utc)
         # clear the all previous output and print the remaining time
         clear_output()
         print(f"Waiting for next full minute to start (remaining time: {remaining_time})...")
      # sleep for a very short time to not overload the CPU
      sleep(0.0000001)
   
   # if verbose is True, print that we are starting to take screenshots now
   if verbose: print("Starting to take screenshot(s) NOW...")
   
   # start taking screenshots
   #while dt.utcnow() <= end_datetime:
   while dt.now(tz.utc) <= end_datetime:
      
      # if verbose is True, print the current datetime
      if verbose:
         # clear the all previous output and print the current datetime
         #clear_output()
         #print(f"Taking screenshot(s) at {utcnow_seconds_str()}...")
         print(f"Taking screenshot(s) at {utcnow_seconds_str()}...")
      # take screenshots of all desired sites
      get_screenshots(join=args.join)
      
      # sleep for the given interval
      sleep(args.interval * 60)
