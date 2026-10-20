(function () {
  var el = document.getElementById('particles-js');
  if (!el) return;
  if (typeof particlesJS !== 'function') return;

  // 用户开了“减少动态效果”就不启动，直接移除容器
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    el.remove();
    return;
  }

  var small = window.innerWidth < 640;

  particlesJS('particles-js', {
    particles: {
      number: { value: small ? 32 : 70, density: { enable: true, value_area: 900 } },
      color: { value: ['#7c9cff', '#c084fc', '#8b93a7'] },
      shape: { type: 'circle' },
      opacity: {
        value: 0.3,
        random: true,
        anim: { enable: true, speed: 0.5, opacity_min: 0.04, sync: false }
      },
      size: {
        value: 2.2,
        random: true,
        anim: { enable: false, speed: 20, size_min: 0.1, sync: false }
      },
      line_linked: {
        enable: true,
        distance: 200,
        color: '#7c9cff',
        opacity: 0.15,
        width: 1
      },
      move: {
        enable: true,
        speed: 2,
        direction: 'none',
        random: false,
        straight: false,
        out_mode: 'out',
        bounce: false,
        attract: { enable: false, rotateX: 3000, rotateY: 3000 }
      }
    },
    interactivity: {
      detect_on: 'canvas',
      events: {
        onhover: { enable: false, mode: 'grab' },
        onclick: { enable: false, mode: 'push' },
        resize: true
      },
      modes: {
        grab: { distance: 150, line_linked: { opacity: 0.3 } },
        bubble: { distance: 200, size: 80, duration: 0.4 },
        repulse: { distance: 200, duration: 0.4 },
        push: { particles_nb: 3 },
        remove: { particles_nb: 2 }
      }
    },
    retina_detect: true
  });
})();