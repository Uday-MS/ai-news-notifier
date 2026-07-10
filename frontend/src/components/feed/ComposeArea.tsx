export function ComposeArea() {
  return (
    <div className="px-4 py-3 border-b border-outline flex gap-3">
      <div className="w-10 h-10 shrink-0 rounded-full overflow-hidden bg-surface-container">
        <img
          className="w-full h-full object-cover"
          alt="Your avatar"
          src="https://lh3.googleusercontent.com/aida-public/AB6AXuDvbqKyoRICsCrs_UUchCm9nugnO9h52QKYHuNBqyQs47GXJnQc8EP7d7n4FGw94gACagI3A4WmB7CVf05hlQeFSqxm0Dy_ZdyHhNCIIp02_k9jStrk3cf-pIBrODIQloYY5SX15VtlRxCWLg1QcnwEb9GFPJ10nmnwO-F1vvqykbzypgzTzOlyzcoxvK6mhYTj-vqK84HXpT-7yEphxTqt_UhNOGCBLOA4fRtF70mn8Fjt_mULZvhB_fWXlGf4pM3QQmNdFcdOAwo"
        />
      </div>
      <div className="flex-1 flex flex-col gap-3">
        <textarea
          className="w-full bg-transparent border-none resize-none focus:ring-0 p-0 text-xl font-body text-on-surface placeholder:text-on-surface-variant h-14 outline-none"
          placeholder="What's happening in AI?"
        />
        <div className="flex justify-between items-center pt-2 border-t border-outline">
          <div className="flex gap-1 text-primary">
            <button className="p-2 hover:bg-primary/10 rounded-full transition-colors flex items-center justify-center bg-transparent border-none cursor-pointer text-inherit">
              <span className="material-symbols-outlined text-xl">image</span>
            </button>
            <button className="p-2 hover:bg-primary/10 rounded-full transition-colors flex items-center justify-center bg-transparent border-none cursor-pointer text-inherit">
              <span className="material-symbols-outlined text-xl">bar_chart</span>
            </button>
            <button className="p-2 hover:bg-primary/10 rounded-full transition-colors flex items-center justify-center bg-transparent border-none cursor-pointer text-inherit">
              <span className="material-symbols-outlined text-xl">code</span>
            </button>
          </div>
          <button className="bg-primary text-on-primary px-5 py-2 rounded-full font-bold text-sm hover:opacity-90 transition-opacity border-none cursor-pointer">
            Post
          </button>
        </div>
      </div>
    </div>
  );
}
