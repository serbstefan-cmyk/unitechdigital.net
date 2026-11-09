document.getElementById('y').textContent = new Date().getFullYear();

const header = document.getElementById('top');
const onScroll = () => header.classList.toggle('fixed', window.scrollY > 520);
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

const io = 'IntersectionObserver' in window ? new IntersectionObserver((entries) => {
  entries.forEach((e) => {
    if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
  });
}, { threshold: 0.12 }) : null;
document.querySelectorAll('.reveal').forEach((el, i) => {
  el.style.transitionDelay = (i % 3) * 0.08 + 's';
  if (io) { io.observe(el); } else { el.classList.add('in'); }
});

document.addEventListener('click', (e) => {
  const open = document.querySelector('.lang[open]');
  if (open && !open.contains(e.target)) open.removeAttribute('open');
});
