/* App Engine Console client-side functionality
 *
 * This file is part of App Engine Console.
 *
 * App Engine Console is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, version 3 of the License.
 *
 * App Engine Console is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with App Engine Console; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
 */

//(function() {

var ps1 = '>>> ';
var ps2 = '... ';

var hist = {
    'buffer'  : [],
    'position': -1,
    'pending' : ''
};

// Processing begins here.
var main = function() {
    console.debug('Starting');

    // Event handlers
    $('#console_form').submit(statementSubmit);
    $('#console_statement').keyup(statementKeyUp);
    $('#setting_teamwork').change(setTeamwork);

    // Some browsers cache the <select> option, so do the teamwork thing now.
    setTeamwork();

    fetchBanner();

    var input = $('#console_statement').get(0);
    if(input != null)
        input.focus();
};

var statementSubmit = function(event) {
    try {
        var input = $('#console_statement');
        var statement = input.val();
        console.debug('Statement submitted: %s', statement);

        input.val('');

        if(statement == 'clear') {
            $('#console_output').html('');
            $('#console_area').get(0).scrollTop = 0;
            return;
        }

        var id = 'statement_' + uid();
        var statementContainer = $('<div>')
            .addClass('code')
            .addClass('pygments').append(
                // This is a temporary representation of the code.  When the server replies,
                // it will re-send the code that it processed (usually marked up with syntax
                // highlighting), upon which we will replace this with the server's version.
                $('<span>')
                    .addClass('code')
                    .append(statement)
            );

        $('#console_output').append(statementContainer).append('<br />');

        // Bring the history up to date.
        hist.buffer.push(statement);
        hist.position = -1;
        hist.pending  = '';

        // POST the statement to the servre.
        var highlight = ( $('#setting_highlight').val() == 'Highlighting' )
            ? 1
            : 0;

        var values = {
            'session'  : $('#setting_session').val(),
            'highlight': highlight,
            'code'     : statement
        };

        var returnedStatement = function(response, textStatus) {
            // Handle the response returned from Python on the server.
            switch(textStatus) {
                case 'timeout':
                case 'error':
                case 'notmodified':
                case 'parseerror':
                    console.error('Statement error: %s; response=%s', textStatus, response);
                    return;
                    break;
            }

            // Replace the old temporarary code with the server's version.
            statementContainer.html(response.in);

            // Append the server output.
            if(response.out && response.out.length) {
                if(highlight)
                    $('#console_output').append(
                        $('<div>')
                            .addClass('pygments')
                            .addClass('data')
                            .append(response.out)
                    );
                else {
                    $('#console_output').append(
                        $('<span>')
                            .addClass('data')
                            .append(response.out)
                    ).append('<br/>');
                }

                scrollOutput();
            }

            showPrompt(response.result);
        };

        $.post('/console/statement', values, returnedStatement, 'json');

        scrollOutput();
    }
    finally {
        event.preventDefault();
    }
};

var statementKeyUp = function(event) {
    var orig = event.originalEvent;
    var key = event.charCode || event.keyCode || 0;

    if(orig.shiftKey) {
        // Support TTY-style Shift-PageUp and Shift-PageDown functionality.
        if     (key == 33)
            scroll('up');
        else if(key == 34)
            scroll('down');
    }

    if(orig.shiftKey || orig.altKey || orig.metaKey || orig.ctrlKey) {
        console.debug('Ignoring keypress with a modifier key');
        return;
    }

    if     (key == 38)
        moveHistory(-1);
    else if(key == 40)
        moveHistory(1);
};

var scroll = function(dir) {
    //console.debug('Scrolling: %s', dir);
    var area = $('#console_area').get(0);
    var scrollDelta = 236;  // This is what it happens to be on my FF3/Fedora system.

    if(area.offsetHeight > area.scrollHeight)
        // The text in the window is too small for scrolling to have happened yet.
        return;

    if(dir == 'up')
        scrollDelta *= -1;

    var newHeight = area.scrollTop + scrollDelta;
    if(newHeight < 0)
        newHeight = 0;
    if(newHeight > area.scrollHeight)
        newHeight = area.scrollHeight;

    area.scrollTop = newHeight;
};

var fetchBanner = function() {
    var gotBanner = function(response, textStatus) {
        // Handle the banner from the console.
        var banner = $('<span>');

        if(textStatus == 'success')
            banner.addClass('banner').append(response.banner);
        else {
            console.error('Banner error: %s; response=%s', textStatus, response);
            banner.addClass('error').append('(Failed to fetch Python banner)');
        }
        $('#console_output').append(banner).append('<br />');

        showPrompt();
    };

    $.get('/console/banner', {}, gotBanner, 'json');
};

var showPrompt = function(continuing) {
    var promptStr = continuing ? ps2 : ps1;
    $('#console_output').append(
        $('<span>').addClass('code').append(promptStr)
    );

    scrollOutput();
};

var cls = function() {
    console.debug('Clearing screen');
};

var moveHistory = function(delta) {
    // totally bogus value
    if (delta == 0 || hist.buffer.length == 0)
        return;

    var input = $('#console_statement');

    if (hist.position == -1) {
        hist.pending = input.val();
        if (delta > 0)
            return;
        hist.position = hist.buffer.length - 1;
        input.val(hist.buffer[hist.position]);
        return;
    }

    if (hist.position == 0 && delta < 0)
        return;

    if (hist.position == hist.buffer.length - 1 && delta > 0) {
        hist.position = -1;
        input.val(hist.pending);
        return;
    }

    hist.position += delta;
    input.val(hist.buffer[hist.position]);
};

var scrollOutput = function() {
    var area = $('#console_area').get(0);

    var last = $('#console_output').children().slice(-1).get(0);
    if((typeof(last) == 'undefined') || (last == null))
        return;

    if(area.offsetHeight > area.scrollHeight)
        area.scrollTop = 0;
    else
        area.scrollTop = area.scrollHeight;
};

var setTeamwork = function(event) {
    /* Handle the various teamwork settings. */
    var choice     = $('#setting_teamwork').val();
    var talkinator = $('#talkinator');
    var pastebin   = $('#pastebin');
    var console    = $('#console_interface');

    /* Talkinator stuff */
    var showTalkinator = function() {
        var room = $('#setting_room').val();
        var widgetWidth = 250;
        var consoleOffset = widgetWidth + 10;

        console.width(console.width() - consoleOffset);
        talkinator.width(widgetWidth);
        talkinator.css('display', 'block');
        talkinator.html(
            '<iframe width="' + widgetWidth + '" height="540" marginwidth="0" marginheight="0" scrolling="no"' +
            '       style="border: 2px solid #93b7fa" frameborder="0"'                         +
            '       src="http://t8r4.info/$r?s=0&t=h&w=250&h=540&c=93b7fa&b=' + room + '"> '   +
            '</iframe>');
    };

    var hideTalkinator = function() {
        talkinator.html('');
        talkinator.css('display', 'none');
        talkinator.width(0);
        console.width('100%');
    };

    /* Pastebin stuff */
    var showPastebin = function() {
        pastebin.css('display', 'block');
        pastebin.html(
            '<iframe width="100%" height="400" marginwidth="0" marginheight="0" scrolling="yes"' +
            '       style="border: 2px solid #93b7fa" frameborder="0"'                          +
            '       src="http://pastebin.com/"> '                                               +
            '</iframe>');
    };

    var hidePastebin = function() {
        pastebin.html('');
        pastebin.css('display', 'none');
    };

    if(choice == 'Chatting') {
        hidePastebin();
        showTalkinator();
    }
    else if(choice == 'Pastebin') {
        hideTalkinator();
        showPastebin();
    }
    else {
        hidePastebin();
        hideTalkinator();
    }
};

/* Generate IDs unique for the current page load. It uses a closure to maintain state. */
var uid = (function() {
        var id = 0;
        return function() {
            return id++;
        };
    }
)();

//
// __END__
//

// Support no-op logging in a non-Firebug environment.
try {
    console;
}
catch(e) {
    var noop = function() {};
    console = {
        'debug' : noop,
        'info'  : noop,
        'error' : noop
    };
}

$(document).ready(main);

//})();
