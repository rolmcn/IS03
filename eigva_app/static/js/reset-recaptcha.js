function resetRecaptcha() {
        if (grecaptcha) {
          grecaptcha.reset();
        }
      }

      {% if success %}
        window.onload = resetRecaptcha;
      {% endif %}