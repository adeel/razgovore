def urls_to_links(text):
  """Attempt to find URLs within the text and convert them to HTML links.
     Most common TLDs are supported."""
  
  import string as s
  domain_valid_chars = s.letters + s.digits + '.-'
  url_valid_chars = domain_valid_chars + ':/~!@#$%^&*()_=+?'
  
  punctuation = '.,?-()'
  
  new_window_attr = ' onclick="return !window.open(this.href);"'
  
  def extract_punc(string):
    """Split a string into three parts:
       any punctuation before, the actual string, and any punctuation after."""
    punc_before = ''
    punc_after = ''
    for c in string:
      if c in punctuation: punc_before += c
      else: break
    for c in string[::-1]:
      if c in punctuation: punc_after += c
      else: break
    punc_after = punc_after[::-1]
    string_stripped = string.strip(punc_before + punc_after)
    return punc_before, string_stripped, punc_after
  
  def chop_string(string):
    """Split a string into its pieces, chopping at "invalid characters"."""
    chopping_board = []
    for char in string:
      if char in url_valid_chars and len(chopping_board) > 0:
        previous = chopping_board[-1]
        if len(previous) == 1 and previous not in url_valid_chars:
          chopping_board.append(char)
        else: chopping_board[-1] += char
      else: chopping_board.append(char)
    return chopping_board
  
  tlds = ['com', 'org', 'edu', 'net', 'info', 'name', 'us', 'uk', 'ca', 'gov']
  
  converted = ''
  for part in chop_string(text):
    if len(part) == 1 and part not in url_valid_chars:
      converted += part
    else:
      punc_before, part_stripped, punc_after = extract_punc(part)
      link = part_stripped
      if not link.startswith('http://'): link = 'http://' + link
      url_parts = part_stripped.partition('.')
      tld = url_parts[2].partition('/')[0]
      if part_stripped.startswith('http://') or part_stripped.startswith('www.') or (all(url_parts) and tld in tlds):
        part = punc_before + '<a href="' + link + '"' + new_window_attr + '>' + part_stripped + '</a>' + punc_after
      converted += part
  # converted = converted.replace('http://<a href="http://', '<a href="http://')
  return converted

def latex(text):
  """Parse text between dollar signs as LaTeX and convert the result to an image.
     Unpaired dollar signs are left alone."""
  
  def is_url_valid(url):
    """Check if a URL is valid."""
    import urllib2
    req = urllib2.Request(url)
    try: urllib2.urlopen(req)
    except urllib2.HTTPError: return False
    return True
  
  def get_latex_img_url(exp):
    """Take a LaTeX expression and get the URL of AoPS's cached image of it."""
    import sha
    h = sha.new(exp).hexdigest()
    url = 'http://alt1.artofproblemsolving.com/Forum/latexrender/pictures/%s/%s/%s/%s.gif' % (h[0], h[1], h[2], h)
    if not is_url_valid(url):
      import urllib, urllib2
      data = urllib.urlencode({'textarea': exp})
      try: req = urllib2.Request('http://www.artofproblemsolving.com/LaTeX/AoPS_L_TeXer.php', data)
      except urllib2.HTTPError: return False
      texer_src = urllib2.urlopen(req).read()
      from BeautifulSoup import BeautifulSoup
      url = BeautifulSoup(texer_src).findAll("img", alt=True, align="absmiddle")[0]['src']
    return url
  
  literal_dollar_sign = '<:razgovore-dollar-sign>'
  
  text = text.replace('\$', literal_dollar_sign)
  import re
  exps = re.compile('\$[^\$]+\$').finditer(text)
  offset = 0
  for exp in exps:
    a = exp.start() + offset
    b = exp.end() + offset
    exp = text[a+1:b-1]
    exp = exp.replace(literal_dollar_sign, '\$')
    exp_ = encode_unicode(exp)
    url = get_latex_img_url(exp)
    if not url: break
    html = '<img src="%s" alt="%s" title="%s" class="latex" />' % (url, exp_, exp_)
    text = text[:a] + html + text[b:]
    offset += len(html) - len(exp) - 2
  text = text.replace(literal_dollar_sign, '$')
  return text
