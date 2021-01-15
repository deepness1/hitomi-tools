# hitomi-tools
hitomi-tools is a small utilities writen in Python3.  
Can be used to search and scrape the works of hitomi.la.

## Requirement
Python3 installed.
No other modules required.

## Example
List works that contain [female:big breasts" female:sister group]:
```
python hitomi-search.py -t "female:big breasts" female:sister group
```
List Japanese original works:
```
python hitomi-search.py -s original -l japanese
```
Download two works with id ["1825469" "1825467"]:
```
python hitomi-download.py 1825469 1825467
```
Download all english doujinshi to "dl" folder:
```
python hitomi-search.py -w doujinshi -l english | python hitomi-download.py -o dl
```
