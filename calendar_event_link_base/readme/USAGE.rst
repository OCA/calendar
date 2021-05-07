* Inherit the `calendar.event.link.mixin` to the model you want to extend

.. code-block:: python

    class YourModel(models.Model):
        _name = 'your.model'
        _inherit = ['your.model', 'calendar.event.link.mixin']

* Inherit the form view of your model and add this button to the `button_box` `div`

.. code-block:: xml

    <button class="oe_stat_button" type="object" name="action_show_events" icon="fa-calendar">
        <div class="o_stat_info">
            <field name="event_count" class="o_stat_value"/>
            <span class="o_stat_text" attrs="{'invisible': [('event_count', '&lt;', 2)]}">Meetings</span>
            <span class="o_stat_text" attrs="{'invisible': [('event_count', '&gt;', 1)]}">Meeting</span>
        </div>
    </button>

