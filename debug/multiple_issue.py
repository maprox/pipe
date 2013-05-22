import urllib.request
import urllib.parse

url = 'http://observer.maprox.net/mon_packet/create'
url_data = {
  'list': '[{"uid":"7142052E-8BE3-4AF8-ACA0-417B8E3AB6D1","altitude":155,"latitude":55.87849940862536,"longitude":37.6821538369437,"accuracy":65,"device_key":"2575888acb19153f957d7f87b0ea231a","time":"2013-05-14T18:33:50"},{"uid":"7142052E-8BE3-4AF8-ACA0-417B8E3AB6D1","altitude":155,"latitude":55.87848755773328,"longitude":37.68226730259056,"accuracy":290.3795899572604,"device_key":"2575888acb19153f957d7f87b0ea231a","time":"2013-05-14T18:34:06"},{"uid":"7142052E-8BE3-4AF8-ACA0-417B8E3AB6D1","altitude":155,"latitude":55.87848755773328,"longitude":37.68226730259056,"accuracy":290.3795899572604,"device_key":"2575888acb19153f957d7f87b0ea231a","time":"2013-05-14T18:34:03"}]',
  'lang': 'en'
}

invalid_url = url + '?list=' + url_data['list'] + '&lang=en'
#valid_url = url + '?list=[{"uid":"7142052E-8BE3-4AF8-ACA0-417B8E3AB6D1","altitude":155,"latitude":55.87849940862536,"longitude":37.6821538369437,"accuracy":65,"device_key":"2575888acb19153f957d7f87b0ea231a","time":"2013-05-14T18:33:50"},{"uid":"7142052E-8BE3-4AF8-ACA0-417B8E3AB6D1","altitude":155,"latitude":55.87848755773328,"longitude":37.68226730259056,"accuracy":290.3795899572604,"device_key":"2575888acb19153f957d7f87b0ea231a","time":"2013-05-14T18:34:06"}]&lang=en'

print("---INVALID URL---")
json = urllib.request.urlopen(invalid_url)
print(json.read())

print("---VALID URL via POST---")
params = urllib.parse.urlencode(url_data).encode('utf-8')
request = urllib.request.Request(url)
request.add_header("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")
connection = urllib.request.urlopen(request, params)
print(connection.read())