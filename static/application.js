soundManager.debugMode = false;
soundManager.url = '/static/';
soundManager.defaultOptions.volume = 100;

var Application = {
  is_focused: true,
  is_input_focused: false,
  
  init: function() {
    
    var self = this;
    
    $('loading').hide();

    Application.room = document.body.getAttribute('room');
    Application.user = document.body.getAttribute('user');

    Application.Users.init();
    Application.Messages.init();
    Application.Rooms.init();
    
    self.update();
    new PeriodicalExecuter(self.update, 2);

    Application.observe_inputs();

    window.onfocus = function() {
      Application.is_focused = true;
      Application.new_messages = 0;
    }

    window.onblur = function() {
      Application.is_focused = false;
    }

    document.onkeypress = function() {
      if (!Application.is_input_focused)
        $('message').focus();
    }

    return true;
  },
  
  update: function() {
    new Ajax.Request('/' + Application.room + '/update', {
      'method': 'get',
      'onSuccess': function(transport) {
        var response = transport.responseText.evalJSON(true);
        Application.Messages.insert_messages(response['messages']);
        Application.Users.fill_list(response['users']);
        Application.Rooms.update_topic(response['topic']);
      }
    });
  }
}

Application.observe_inputs = function() {
  $$('input, textarea').each(function(el) {
    el.observe('focus', function() { Application.is_input_focused = true; });
    el.observe('blur', function() { Application.is_input_focused = false; });
  });
}

Application.scroll_to_bottom = function() {
  if (Application.is_scrolled_to_bottom())
    return;
  if (Application.is_scrolling && !Application.is_scrolling_to_bottom)
    return;

  Application.is_scrolling = true;
  Application.is_scrolling_to_bottom = true;

  var t = $('transcript');
  t.scrollTop = 2 * t.scrollHeight;
  
  Application.is_scrolling = false;
  Application.is_scrolling_to_bottom = false;
}

Application.is_scrolled_to_bottom = function() {
  var t = $('transcript');
  return t.scrollTop + t.clientHeight >= t.scrollHeight;
}

Application.ping = function() {
  soundManager.play('ping', '/static/ping.mp3');
}

Application.Rooms = {
  
  is_topic_being_edited: false,
  
  init: function() {
    var self = this;

    var topic = $('topic');
    if (topic.getAttribute('can_set') == 'True') {
      topic.observe('click', function(e) {
        if (topic.childElements().length != 0) {
          Event.stop(e);
          return false;
        }
        self.is_topic_being_edited = true;
        old_topic = topic.value;
        topic.editable(function(new_topic) {
          new_topic = Application.Rooms.filter(new_topic);
          if (!new_topic) {
            self.update_topic(old_topic);
            return false;
          }
          self.is_topic_being_edited = false;
          self.update_topic(new_topic);
          new Ajax.Request('/' + Application.room + '/topic', {
            'method': 'get', 'parameters': {'topic': new_topic}
          });
        });
      });
    }
  },
  
  update_topic: function(topic) {
    if (!this.is_topic_being_edited)
      $('topic').update(topic);
  },
  
  filter: function(topic) {
    if (!!topic.blank()) return false;
    return topic.escapeHTML().strip().truncate(255, '...');
  }
}

Application.Users = {
  init: function() {
    var self = this;
    
    if ($('register') != null) {
      $('register').hide();
      $('register_link').observe('click', function() {
        Application.Users.show_register_form();
      });
    }
    
    return true;
  },
  
  show_register_form: function() {
    $('register').show();
    $('register').select('#hint')[0].hide();
    $('register').select('input')[0].focus()
    $('register').observe('submit', function() {
      input = this.select('input#password')[0];
      password = input.value;
      if (!Application.Users.is_password_valid(password)) {
        $('register').select('#hint')[0].show();
        return false;
      }
      input.value = '';
      new Ajax.Updater('account', '/register', {
        'method': 'post', 'parameters': {'password': password},
        'onSuccess': function() { $('register').hide(); },
        'onComplete': function() { $('register').hide(); },
        'onLoading': function() { $('loading').show(); },
        'onLoaded': function() { $('loading').hide(); }
      });
    });
  },
  
  is_password_valid: function(password) {
    if (!!password.blank()) return false;
    if (password.length < 5) return false;
    return true;
  },
  
  fill_list: function(users) {
    $('users').select('ul')[0].update(
      users.map(function(u) {return '<li>' + u + '</li>'}).join(''));
  }
};

Application.Messages = {
  init: function() {
    var self = this;
    
    if (!Application.is_input_focused)
      $('message').select();
    
    Application.scroll_to_bottom();
    $('transcript').observe('scroll', function() {
      Application.is_scrolling = true;
      if (Application.is_scrolled_to_bottom()) {
        Application.is_scrolling = false;
        Application.is_scrolling_to_bottom = false;
      }
    });
    
    $('new_message_form').observe('submit', function() {
      if (Application.Messages.last_post != null
      && (Number(new Date()) - Application.Messages.last_post < 500))
        return false;
      else {
        Application.Messages.last_post = Number(new Date());
      }
      message_text = Application.Messages.filter($('message').value);
      if (!message_text) return false;
      new Ajax.Request('/' + Application.room + '/message', {
        'method': 'post', 'parameters': {'message_text': message_text},
        'onSuccess': function() {
          Application.update();
          $('message').value = '';
        },
        'onLoading': function() { $('loading').show(); },
        'onLoaded': function() { $('loading').hide(); }
      });
      return false;
    });
    
    // new PeriodicalExecuter(function() {
    //   if (!Application.is_input_focused) $('message').focus();
    // }, 5);
    
    new PeriodicalExecuter(function() { Application.scroll_to_bottom(); }, 0.5);
    
    return true;
  },
  
  filter: function(text) {
    if (!!text.blank()) return false;
    // text = text.escapeHTML();
    text = text.strip();
    text = text.truncate(255, '...');
    return text;
  },
  
  insert_messages: function(messages) {
    var self = this;
    
    transcript = $('transcript').select('table')[0];
    messages.each(function(m) {
      
      if ((m['user_name'] != Application.user) && !m['user_name'].startsWith('System/')) {
        m['message_text'] = self.highlight(m['message_text']);
      }
      
      all_messages = transcript.select('tr');
      var row = new Element('tr', {'class': 'row'});
      if (m['user_name'].startsWith('System/'))
        row.addClassName('notification');
      if (m['user_name'] == 'System/time') {
        row.addClassName('time');
        m['message_text'] = strftime(new Date(), '%I:%M %p');
        if (m['message_text'].startsWith('0'))
          m['message_text'] = m['message_text'].substring(1);
      }
      if ((all_messages.length == 0) || (all_messages.last().select('td.user_name')[0].innerHTML != m['user_name']))
        row.addClassName('first');
      else
        row.addClassName('not-first');
      var col_user = new Element('td', {'class': 'user_name'}).update(m['user_name']);
      var col_text = new Element('td', {'class': 'message_text'}).update(m['message_text']);
      if (m['user_name'] == 'System/time') {
        times = transcript.select('tr.time');
        if ((times.length > 0) && (times.last() == all_messages.last()))
          times.last().addClassName('time-replaced');
      }
      row.insert(col_user, {position: 'bottom'});
      row.insert(col_text, {position: 'bottom'});
      transcript.insert(row, {position: 'bottom'});
    });
  },
  
  highlight: function(text) {
    var u = Application.user;
    var match = new RegExp ("\\b(" + u + ")\\b", 'g')
    if (match.test(text))
      Application.ping();
    return text.replace(match, '<span class="highlight">' + u + '</span>');
  },
  
  after_update: function() {
    Application.scroll_to_bottom();
  }
}

Element.prototype.editable = function(oncomplete) {
  self = this;
  this.update('<form style="margin:0"><input type="text" value="' + this.innerHTML + '" /></form>');
  Application.observe_inputs();
  var form = this.down();
  var input = form.down();
  // input.select();
  // input.focus();
  finished = function(e) {
    Event.stop(e);
    form.stopObserving('submit');
    input.stopObserving('blur');
    var new_value = input.value;
    self.update(new_value);
    oncomplete(new_value);
    return false;
  };
  form.observe('submit', finished);
  input.observe('blur', finished);
}

strftime = function(date, format) {
  // modified from http://alternateidea.com/blog/articles/2008/2/8/a-strftime-for-prototype
  var day = date.getDay(), month = date.getMonth();
  var hours = date.getHours(), minutes = date.getMinutes();
  function pad(num) { return num.toPaddedString(2); };

  return format.gsub(/\%([aAbBcdDHiImMpSwyY])/, function(part) {
    switch(part[1]) {
      case 'a': return $w("Sun Mon Tue Wed Thu Fri Sat")[day]; break;
      case 'A': return $w("Sunday Monday Tuesday Wednesday Thursday Friday Saturday")[day]; break;
      case 'b': return $w("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec")[month]; break;
      case 'B': return $w("January February March April May June July August September October November December")[month]; break;
      case 'c': return date.toString(); break;
      case 'd': return date.getDate(); break;
      case 'D': return pad(date.getDate()); break;
      case 'H': return pad(hours); break;
      case 'i': return (hours === 12 || hours === 0) ? 12 : (hours + 12) % 12; break;
      case 'I': return pad((hours === 12 || hours === 0) ? 12 : (hours + 12) % 12); break;
      case 'm': return pad(month + 1); break;
      case 'M': return pad(minutes); break;
      case 'p': return hours > 11 ? 'PM' : 'AM'; break;
      case 'S': return pad(date.getSeconds()); break;
      case 'w': return day; break;
      case 'y': return pad(date.getFullYear() % 100); break;
      case 'Y': return date.getFullYear().toString(); break;
    }
  });
}