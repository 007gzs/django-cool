/*global Calendar, findPosX, findPosY, get_format, gettext, gettext_noop, interpolate, ngettext, quickElement*/
// Inserts shortcut buttons after all of the following:
//     <input type="text" class="vDateField">
//     <input type="text" class="vTimeField">
(function($) {
    'use strict';
    var RangeDateShortcuts = {
        calendars: [],
        calendarInputs: [],
        dismissClockFunc: [],
        dismissCalendarFunc: [],
        calendarDivName1: 'calendarbox', // name of calendar <div> that gets toggled
        calendarDivName2: 'calendarin', // name of <div> that contains calendar
        calendarLinkName: 'calendarlink', // name of the link that is used to toggle
        shortCutsClass: 'datetimeshortcuts', // class of the clock and cal shortcuts
        timezoneWarningClass: 'timezonewarning', // class of the warning for timezone mismatch
        dateInputFormats: '%Y-%m-%d',
        timezoneOffset: 0,
        init: function() {
            var body = document.getElementsByTagName('body')[0];
            var serverOffset = body.getAttribute('data-admin-utc-offset');
            if (serverOffset) {
                var localOffset = new Date().getTimezoneOffset() * -60;
                RangeDateShortcuts.timezoneOffset = localOffset - serverOffset;
            }

            var inputs = document.getElementsByTagName('input');
            for (var i = 0; i < inputs.length; i++) {
                var inp = inputs[i];
                if (inp.getAttribute('type') === 'text' && inp.className.match(/vDateFieldInRange/)) {
                    RangeDateShortcuts.addCalendar(inp);
                    RangeDateShortcuts.addTimezoneWarning(inp);
                }
            }
        },
        // Return the current time while accounting for the server timezone.
        now: function() {
            var body = document.getElementsByTagName('body')[0];
            var serverOffset = body.getAttribute('data-admin-utc-offset');
            if (serverOffset) {
                var localNow = new Date();
                var localOffset = localNow.getTimezoneOffset() * -60;
                localNow.setTime(localNow.getTime() + 1000 * (serverOffset - localOffset));
                return localNow;
            } else {
                return new Date();
            }
        },
        // Add a warning when the time zone in the browser and backend do not match.
        addTimezoneWarning: function(inp) {
            var warningClass = RangeDateShortcuts.timezoneWarningClass;
            var timezoneOffset = RangeDateShortcuts.timezoneOffset / 3600;

            // Only warn if there is a time zone mismatch.
            if (!timezoneOffset) {
                return;
            }

            // Check if warning is already there.
            if (inp.parentNode.querySelectorAll('.' + warningClass).length) {
                return;
            }

            var message;
            if (timezoneOffset > 0) {
                message = ngettext(
                    'Note: You are %s hour ahead of server time.',
                    'Note: You are %s hours ahead of server time.',
                    timezoneOffset
                );
            }
            else {
                timezoneOffset *= -1;
                message = ngettext(
                    'Note: You are %s hour behind server time.',
                    'Note: You are %s hours behind server time.',
                    timezoneOffset
                );
            }
            message = interpolate(message, [timezoneOffset]);

            var warning = document.createElement('span');
            warning.className = warningClass;
            warning.textContent = message;
            inp.parentNode.appendChild(document.createElement('br'));
            inp.parentNode.appendChild(warning);
        },
        // Add calendar widget to a given field.
        addCalendar: function(inp) {
            var num = RangeDateShortcuts.calendars.length;

            RangeDateShortcuts.calendarInputs[num] = inp;
            RangeDateShortcuts.dismissCalendarFunc[num] = function() { RangeDateShortcuts.dismissCalendar(num); return true; };
            inp.addEventListener('click', function(e) {
                e.preventDefault();
                // avoid triggering the document click handler to dismiss the calendar
                e.stopPropagation();
                for (var i = 0; i < RangeDateShortcuts.calendars.length; i ++) {
                    if(i !== num) {
                        RangeDateShortcuts.dismissCalendarFunc[i]();
                    }
                }
                RangeDateShortcuts.openCalendar(num);
            });

            // Create calendarbox div.
            //
            // Markup looks like:
            //
            // <div id="calendarbox3" class="calendarbox module">
            //     <h2>
            //           <a href="#" class="link-previous">&lsaquo;</a>
            //           <a href="#" class="link-next">&rsaquo;</a> February 2003
            //     </h2>
            //     <div class="calendar" id="calendarin3">
            //         <!-- (cal) -->
            //     </div>
            //     <div class="calendar-shortcuts">
            //          <a href="#">Yesterday</a> | <a href="#">Today</a> | <a href="#">Tomorrow</a>
            //     </div>
            //     <p class="calendar-cancel"><a href="#">Cancel</a></p>
            // </div>
            var cal_box = document.createElement('div');
            cal_box.style.display = 'none';
            cal_box.style.position = 'absolute';
            cal_box.style.zIndex = '2000';
            cal_box.className = 'calendarbox module';
            cal_box.setAttribute('id', RangeDateShortcuts.calendarDivName1 + num);
            document.body.appendChild(cal_box);
            cal_box.addEventListener('click', function(e) { e.stopPropagation(); });

            // next-prev links
            var cal_nav = quickElement('div', cal_box);
            var cal_nav_prev = quickElement('a', cal_nav, '<', 'href', '#');
            cal_nav_prev.className = 'calendarnav-previous';
            cal_nav_prev.addEventListener('click', function(e) {
                e.preventDefault();
                RangeDateShortcuts.drawPrev(num);
            });

            var cal_nav_next = quickElement('a', cal_nav, '>', 'href', '#');
            cal_nav_next.className = 'calendarnav-next';
            cal_nav_next.addEventListener('click', function(e) {
                e.preventDefault();
                RangeDateShortcuts.drawNext(num);
            });

            // main box
            var cal_main = quickElement('div', cal_box, '', 'id', RangeDateShortcuts.calendarDivName2 + num);
            cal_main.className = 'calendar';
            RangeDateShortcuts.calendars[num] = new Calendar(RangeDateShortcuts.calendarDivName2 + num, RangeDateShortcuts.handleCalendarCallback(num));
            RangeDateShortcuts.calendars[num].drawCurrent();

            // calendar shortcuts
            var shortcuts = quickElement('div', cal_box);
            shortcuts.className = 'calendar-shortcuts';
            var day_link = quickElement('a', shortcuts, gettext('Yesterday'), 'href', '#');
            day_link.addEventListener('click', function(e) {
                e.preventDefault();
                RangeDateShortcuts.handleCalendarQuickLink(num, -1);
            });
            shortcuts.appendChild(document.createTextNode('\u00A0|\u00A0'));
            day_link = quickElement('a', shortcuts, gettext('Today'), 'href', '#');
            day_link.addEventListener('click', function(e) {
                e.preventDefault();
                RangeDateShortcuts.handleCalendarQuickLink(num, 0);
            });
            shortcuts.appendChild(document.createTextNode('\u00A0|\u00A0'));
            day_link = quickElement('a', shortcuts, gettext('Tomorrow'), 'href', '#');
            day_link.addEventListener('click', function(e) {
                e.preventDefault();
                RangeDateShortcuts.handleCalendarQuickLink(num, +1);
            });

            // cancel bar
            var cancel_p = quickElement('p', cal_box);
            cancel_p.className = 'calendar-cancel';
            var cancel_link = quickElement('a', cancel_p, gettext('Cancel'), 'href', '#');
            cancel_link.addEventListener('click', function(e) {
                e.preventDefault();
                RangeDateShortcuts.dismissCalendar(num);
            });
            document.addEventListener('keyup', function(event) {
                if (event.which === 27) {
                    // ESC key closes popup
                    RangeDateShortcuts.dismissCalendar(num);
                    event.preventDefault();
                }
            });
        },
        openCalendar: function(num) {
            var cal_box = document.getElementById(RangeDateShortcuts.calendarDivName1 + num);
            var inp = RangeDateShortcuts.calendarInputs[num];

            // Determine if the current value in the input has a valid date.
            // If so, draw the calendar with that date's year and month.
            if (inp.value) {
                var format = RangeDateShortcuts.dateInputFormats;
                var selected = inp.value.strptime(format);
                var year = selected.getUTCFullYear();
                var month = selected.getUTCMonth() + 1;
                var re = /\d{4}/;
                if (re.test(year.toString()) && month >= 1 && month <= 12) {
                    RangeDateShortcuts.calendars[num].drawDate(month, year, selected);
                }
            }

            // Recalculate the clockbox position
            // is it left-to-right or right-to-left layout ?
            if (window.getComputedStyle(document.body).direction !== 'rtl') {
                cal_box.style.left = findPosX(inp) - 180 + 'px';
            }
            else {
                // since style's width is in em, it'd be tough to calculate
                // px value of it. let's use an estimated px for now
                // TODO: IE returns wrong value for findPosX when in rtl mode
                //       (it returns as it was left aligned), needs to be fixed.
                cal_box.style.left = findPosX(inp) + 17 + 'px';
            }
            cal_box.style.top = Math.max(0, findPosY(inp) + 30) + 'px';

            cal_box.style.display = 'block';
            document.addEventListener('click', RangeDateShortcuts.dismissCalendarFunc[num]);
        },
        dismissCalendar: function(num) {
            document.getElementById(RangeDateShortcuts.calendarDivName1 + num).style.display = 'none';
            document.removeEventListener('click', RangeDateShortcuts.dismissCalendarFunc[num]);
        },
        drawPrev: function(num) {
            RangeDateShortcuts.calendars[num].drawPreviousMonth();
        },
        drawNext: function(num) {
            RangeDateShortcuts.calendars[num].drawNextMonth();
        },
        handleCalendarCallback: function(num) {
            var format = RangeDateShortcuts.dateInputFormats;
            // the format needs to be escaped a little
            format = format.replace('\\', '\\\\')
                .replace('\r', '\\r')
                .replace('\n', '\\n')
                .replace('\t', '\\t')
                .replace("'", "\\'");
            return function(y, m, d) {
                var old_value = RangeDateShortcuts.calendarInputs[num].value;
                RangeDateShortcuts.calendarInputs[num].value = new Date(y, m - 1, d).strftime(format);
                RangeDateShortcuts.calendarInputs[num].focus();
                if(old_value !== RangeDateShortcuts.calendarInputs[num].value) {
                    $(RangeDateShortcuts.calendarInputs[num]).trigger("change");
                }
                document.getElementById(RangeDateShortcuts.calendarDivName1 + num).style.display = 'none';
            };
        },
        handleCalendarQuickLink: function(num, offset) {
            var d = RangeDateShortcuts.now();
            d.setDate(d.getDate() + offset);
            RangeDateShortcuts.calendarInputs[num].value = d.strftime(RangeDateShortcuts.dateInputFormats);
            RangeDateShortcuts.calendarInputs[num].focus();
            RangeDateShortcuts.dismissCalendar(num);
        }
    };

    window.addEventListener('load', RangeDateShortcuts.init);
    window.RangeDateShortcuts = RangeDateShortcuts;
})(django.jQuery);
