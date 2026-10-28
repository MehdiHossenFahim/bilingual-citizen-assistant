import { useState, useEffect } from 'react';

/**
 * Animated typewriter placeholder hook for chat textarea.
 * Cycles smoothly through an array of suggested citizen questions.
 * Automatically cleans up timeouts and resets upon language change.
 */
export function useTypewriterPlaceholder(
  phrases = [],
  {
    typingSpeed = 45,
    deletingSpeed = 25,
    pauseDuration = 2200,
    pauseBetween = 350,
    enabled = true,
  } = {}
) {
  const [displayText, setDisplayText] = useState('');
  const [phraseIndex, setPhraseIndex] = useState(0);
  const [charIndex, setCharIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  // Reset when phrases array changes (e.g. language toggle)
  useEffect(() => {
    setPhraseIndex(0);
    setCharIndex(0);
    setIsDeleting(false);
    if (phrases && phrases.length > 0) {
      setDisplayText(phrases[0].slice(0, 1));
      setCharIndex(1);
    } else {
      setDisplayText('');
    }
  }, [phrases]);

  useEffect(() => {
    if (!enabled || !phrases || phrases.length === 0) return;

    const currentPhrase = phrases[phraseIndex % phrases.length];

    if (!isDeleting) {
      // Finished typing current phrase
      if (charIndex >= currentPhrase.length) {
        const timeout = setTimeout(() => {
          setIsDeleting(true);
        }, pauseDuration);
        return () => clearTimeout(timeout);
      }

      // Typing next character
      const timeout = setTimeout(() => {
        setDisplayText(currentPhrase.slice(0, charIndex + 1));
        setCharIndex((prev) => prev + 1);
      }, typingSpeed);
      return () => clearTimeout(timeout);
    } else {
      // Finished deleting current phrase
      if (charIndex <= 0) {
        const timeout = setTimeout(() => {
          setIsDeleting(false);
          setPhraseIndex((prev) => (prev + 1) % phrases.length);
          setCharIndex(0);
        }, pauseBetween);
        return () => clearTimeout(timeout);
      }

      // Deleting character
      const timeout = setTimeout(() => {
        setDisplayText(currentPhrase.slice(0, charIndex - 1));
        setCharIndex((prev) => prev - 1);
      }, deletingSpeed);
      return () => clearTimeout(timeout);
    }
  }, [charIndex, isDeleting, phraseIndex, phrases, typingSpeed, deletingSpeed, pauseDuration, pauseBetween, enabled]);

  return displayText || (phrases && phrases[0]) || '';
}
