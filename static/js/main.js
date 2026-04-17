console.log('main.js loaded');

document.addEventListener('DOMContentLoaded', function() {
  console.log('DOM ready');

  document.querySelectorAll('.alert').forEach(function(alert) {
    console.log('found alert:', alert.className, 'display:', alert.style.display);
    setTimeout(function() {
      console.log('hiding alert after 4s');
      alert.style.display = 'none';
    }, 4000);
  });

  const closeButtons = document.querySelectorAll('.alert__close');
  closeButtons.forEach(button => {
    button.addEventListener('click', function() {
      this.parentElement.style.display = 'none';
    });
  });
});


document.addEventListener('DOMContentLoaded', function() {
  const closeButtons = document.querySelectorAll('.alert__close');

  closeButtons.forEach(button => {
    button.addEventListener('click', function() {
      const alert = this.parentElement;
      alert.style.display = 'none';
    });
  });

  document.querySelectorAll('.alert').forEach(function(alert) {
    setTimeout(function() {
      alert.style.display = 'none';
    }, 4000);
  });
});