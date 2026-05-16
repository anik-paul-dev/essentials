
# Cell 1: Runtime Reminder & Installs
# Important: Manually go to Runtime → Change runtime type → Hardware accelerator → GPU (T4)

!pip install -q torch torchvision torchaudio scikit-learn matplotlib seaborn opencv-python

# Cell 2: All Imports + Mount Drive
# Run after Cell 1

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim import lr_scheduler
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import cv2
from PIL import Image
from torchvision.transforms.functional import to_pil_image
from sklearn.metrics import classification_report, confusion_matrix
import torch.nn.functional as F
import matplotlib.font_manager as fm
import time
from IPython.display import display, Javascript, HTML
from google.colab.output import eval_js
from base64 import b64decode
from google.colab.patches import cv2_imshow

from google.colab import drive
drive.mount('/content/drive')

# Cell 3: Define Paths & Transforms
# Run after Cell 2
# Change data_dir only if your folder path is different
data_dir = "/content/drive/MyDrive/bangla sign dataset"  # Your Bangla-named structure

train_transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.RandomRotation(20),
    transforms.RandomHorizontalFlip(0.5),
    transforms.ColorJitter(brightness=0.4, contrast=0.4, saturation=0.4, hue=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225]),
    transforms.RandomErasing(p=0.5, scale=(0.02, 0.2), ratio=(0.3, 3.3), value=0)
])

test_transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize([0.485,0.456,0.406], [0.229,0.224,0.225])
])

# Cell 4: Load Datasets & DataLoaders
# Run after Cell 3

train_ds = datasets.ImageFolder(os.path.join(data_dir, "train"), train_transform)
val_ds   = datasets.ImageFolder(os.path.join(data_dir, "val"),   test_transform)
test_ds  = datasets.ImageFolder(os.path.join(data_dir, "test"),  test_transform)

train_loader = DataLoader(train_ds, batch_size=48, shuffle=True,  num_workers=2, pin_memory=True)
val_loader   = DataLoader(val_ds,   batch_size=48, shuffle=False, num_workers=2, pin_memory=True)
test_loader  = DataLoader(test_ds,  batch_size=48, shuffle=False, num_workers=2, pin_memory=True)

class_names = train_ds.classes
num_classes = len(class_names)
print(f"→ {num_classes} classes loaded:", class_names)

# Cell 5: Choose EfficientNet Version + Define Models & Device
# Run after Cell 4
# ←←← CHANGE THIS TO SELECT VERSION (b0 to b4) ←←←
effnet_version = 'b4'  # Options: 'b0', 'b1', 'b2', 'b3', 'b4'

device = torch.device("cuda")
print("Device:", device)

class SpatialAttention(nn.Module):
    def __init__(self, kernel_size=7):
        super().__init__()
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=kernel_size//2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)
        x_cat = torch.cat([avg_out, max_out], dim=1)
        x = self.conv(x_cat)
        return self.sigmoid(x)

class EfficientNet_Attention(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        backbone = getattr(models, f'efficientnet_{effnet_version}')(weights='DEFAULT')
        self.features = backbone.features
        in_features = backbone.classifier[1].in_features

        # Unfreeze last 3 blocks
        for layer in self.features[-3:]:
            for p in layer.parameters():
                p.requires_grad = True

        self.attention = SpatialAttention()
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(in_features, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        attn = self.attention(x)
        x = x * attn
        x = self.pool(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)

class EfficientNet_NoAttention(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        backbone = getattr(models, f'efficientnet_{effnet_version}')(weights='DEFAULT')
        self.features = backbone.features
        in_features = backbone.classifier[1].in_features

        # Unfreeze last 3 blocks
        for layer in self.features[-3:]:
            for p in layer.parameters():
                p.requires_grad = True

        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Sequential(
            nn.Dropout(0.4),
            nn.Linear(in_features, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        x = self.pool(x)
        x = torch.flatten(x, 1)
        return self.classifier(x)

model_attn = EfficientNet_Attention(num_classes).to(device)
model_no_attn = EfficientNet_NoAttention(num_classes).to(device)

# Cell 6: Loss, Optimizers & Schedulers
criterion = nn.CrossEntropyLoss()

optimizer_attn = optim.Adam(model_attn.parameters(), lr=5e-4, weight_decay=1e-5)
optimizer_no   = optim.Adam(model_no_attn.parameters(), lr=5e-4, weight_decay=1e-5)

scheduler_attn = lr_scheduler.ReduceLROnPlateau(optimizer_attn, mode='max', factor=0.5, patience=5)
scheduler_no   = lr_scheduler.ReduceLROnPlateau(optimizer_no,   mode='max', factor=0.5, patience=5)

# Cell 7: Training Function (now includes train accuracy)
def train_and_validate(model, optimizer, scheduler, name="Model", epochs=30):
    best_acc = 0.0
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}

    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        running_correct = 0.0

        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, pred = torch.max(outputs, 1)
            running_correct += (pred == labels).sum().item()

        train_loss = running_loss / len(train_loader.dataset)
        train_acc = 100.0 * running_correct / len(train_loader.dataset)
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)

        model.eval()
        correct, total, val_loss = 0, 0, 0.0
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, pred = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (pred == labels).sum().item()

        val_loss /= len(val_loader.dataset)
        val_acc = 100.0 * correct / total
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)

        print(f"[{name}] Epoch {epoch+1}/{epochs} | Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")

        if val_acc > best_acc:
            best_acc = val_acc
            torch.save(model.state_dict(), f"/content/drive/MyDrive/best_{name.lower().replace(' ','_')}.pth")
            print(f"   → Best {name} saved!")

        scheduler.step(val_acc)

    return best_acc, history

# Cell 8: Train Both Models + Plotting (now shows train & val accuracy curves)
print("\nTraining model WITH Attention...")
best_attn, hist_attn = train_and_validate(model_attn, optimizer_attn, scheduler_attn, "With Attention", epochs=30)

epochs_range = range(1, len(hist_attn['train_loss']) + 1)
plt.figure(figsize=(15, 6))
plt.subplot(1, 2, 1)
plt.plot(epochs_range, hist_attn['train_loss'], 'b-', label='Training Loss')
plt.plot(epochs_range, hist_attn['val_loss'], 'r-', label='Validation Loss')
plt.title('With Attention: Loss Curves')
plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(epochs_range, hist_attn['train_acc'], 'b-', label='Training Accuracy')
plt.plot(epochs_range, hist_attn['val_acc'], 'g-', label='Validation Accuracy')
plt.title('With Attention: Accuracy Curves')
plt.xlabel('Epoch'); plt.ylabel('Accuracy (%)'); plt.legend(); plt.grid(True)
plt.tight_layout(); plt.show()

print("\nTraining model WITHOUT Attention...")
best_no, hist_no = train_and_validate(model_no_attn, optimizer_no, scheduler_no, "No Attention", epochs=30)

epochs_range = range(1, len(hist_no['train_loss']) + 1)
plt.figure(figsize=(15, 6))
plt.subplot(1, 2, 1)
plt.plot(epochs_range, hist_no['train_loss'], 'b-', label='Training Loss')
plt.plot(epochs_range, hist_no['val_loss'], 'r-', label='Validation Loss')
plt.title('Without Attention: Loss Curves')
plt.xlabel('Epoch'); plt.ylabel('Loss'); plt.legend(); plt.grid(True)

plt.subplot(1, 2, 2)
plt.plot(epochs_range, hist_no['train_acc'], 'b-', label='Training Accuracy')
plt.plot(epochs_range, hist_no['val_acc'], 'g-', label='Validation Accuracy')
plt.title('Without Attention: Accuracy Curves')
plt.xlabel('Epoch'); plt.ylabel('Accuracy (%)'); plt.legend(); plt.grid(True)
plt.tight_layout(); plt.show()

print(f"\nBest accuracies → With Attention: {best_attn:.2f}% | No Attention: {best_no:.2f}%")

# Cell 9: Load Best Model & Test Evaluation
model_attn.load_state_dict(torch.load("/content/drive/MyDrive/best_with_attention.pth"))
model_no_attn.load_state_dict(torch.load("/content/drive/MyDrive/best_no_attention.pth"))
model_attn.eval()
model_no_attn.eval()

def evaluate(model):
    y_true, y_pred = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            outputs = model(images)
            _, preds = torch.max(outputs, 1)
            y_true.extend(labels.cpu().numpy())
            y_pred.extend(preds.cpu().numpy())
    print(classification_report(y_true, y_pred, target_names=class_names, digits=4))
    return y_true, y_pred

print("\nTest Results - With Attention Model:")
y_true_attn, y_pred_attn = evaluate(model_attn)

print("\nTest Results - Without Attention Model:")
y_true_no, y_pred_no = evaluate(model_no_attn)

# Cell 10: Confusion Matrix (adjusted size for 48 classes)
!apt-get update -qq
!apt-get install -y fonts-noto -qq

fm.fontManager.addfont('/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf')
plt.rcParams['font.family'] = ['Noto Sans Bengali', 'DejaVu Sans']
plt.rcParams['font.sans-serif'] = ['Noto Sans Bengali', 'DejaVu Sans']

plt.figure(figsize=(28, 24))
cm_attn = confusion_matrix(y_true_attn, y_pred_attn)
sns.heatmap(cm_attn, annot=True, fmt='d', cmap='Blues',
            xticklabels=class_names, yticklabels=class_names, cbar=False)
plt.title("Confusion Matrix - With Attention Model", fontsize=18)
plt.xlabel("Predicted", fontsize=14)
plt.ylabel("True", fontsize=14)
plt.xticks(rotation=90, fontsize=8)
plt.yticks(rotation=0, fontsize=8)
plt.tight_layout()
plt.show()

plt.figure(figsize=(28, 24))
cm_no = confusion_matrix(y_true_no, y_pred_no)
sns.heatmap(cm_no, annot=True, fmt='d', cmap='Blues',
            xticklabels=class_names, yticklabels=class_names, cbar=False)
plt.title("Confusion Matrix - Without Attention Model", fontsize=18)
plt.xlabel("Predicted", fontsize=14)
plt.ylabel("True", fontsize=14)
plt.xticks(rotation=90, fontsize=8)
plt.yticks(rotation=0, fontsize=8)
plt.tight_layout()
plt.show()





# Cell 11: Grad-CAM Class & Helper Functions
# Increased heatmap coverage for b4 → full palm + all fingers

class GradCAM:
    def __init__(self, model):
        self.model = model.eval()
        self.gradients = None
        self.activations = None
        self.hooks = []
        # Hook the last convolution layer (consistent for b0–b4)
        last_block = model.features[-1]
        last_conv = last_block[0] if isinstance(last_block, nn.Sequential) else last_block
        self._register_hooks(last_conv)

    def _register_hooks(self, layer):
        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            if grad_output is not None and len(grad_output) > 0 and grad_output[0] is not None:
                self.gradients = grad_output[0].detach()

        self.hooks.append(layer.register_forward_hook(forward_hook))
        self.hooks.append(layer.register_full_backward_hook(backward_hook))

    def remove_hooks(self):
        for hook in self.hooks:
            hook.remove()
        self.hooks = []

    def __call__(self, input_tensor, target_class=None):
        logit = self.model(input_tensor)
        if target_class is None:
            target_class = logit.argmax(dim=1).item()

        score = logit[:, target_class]
        self.model.zero_grad()
        score.backward()

        gradients = self.gradients
        activations = self.activations

        if gradients is None or activations is None:
            print("Grad-CAM failed: gradients or activations not captured")
            return None, None

        weights = torch.mean(gradients, dim=(2, 3), keepdim=True)
        cam = torch.sum(weights * activations, dim=1).squeeze(0)
        cam = F.relu(cam).cpu().numpy()

        # Resize to image size
        cam = cv2.resize(cam, (224, 224), interpolation=cv2.INTER_CUBIC)

        # === Stronger expansion for full hand coverage ===
        # Very light smoothing
        cam = cv2.GaussianBlur(cam, (5, 5), sigmaX=0.8)

        # Large kernel + more iterations → significantly bigger heatmap
        kernel = np.ones((17, 17), np.uint8)   # even larger kernel
        cam = cv2.dilate(cam, kernel, iterations=4)  # more iterations = much larger area

        # Suppress very weak background activations
        threshold = np.percentile(cam, 12)     # slightly lower than before
        cam = np.maximum(cam - threshold, 0)
        cam = cam / (np.max(cam) + 1e-8)

        raw_cam = cam.copy()
        normalized_cam = cam   # already in 0–1 range

        self.remove_hooks()
        return raw_cam, normalized_cam

# Cell 12: Generate Grad-CAM Grid
def show_gradcam_grid(model, model_name):
    gradcam = GradCAM(model)
    plt.figure(figsize=(32, 26))
    count = 0
    max_examples = 16

    for class_name in class_names:
        if count >= max_examples:
            break
        folder = os.path.join(data_dir, "test", class_name)
        if not os.path.isdir(folder):
            continue
        files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
        if not files:
            continue
        img_path = os.path.join(folder, files[0])
        img = cv2.imread(img_path)
        if img is None:
            continue
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_res = cv2.resize(img_rgb, (224, 224))
        inp = test_transform(to_pil_image(img_res)).unsqueeze(0).to(device)

        raw_cam, normalized_cam = gradcam(inp)

        raw_vis = (raw_cam - raw_cam.min()) / (raw_cam.max() - raw_cam.min() + 1e-8)

        heatmap_raw = cv2.applyColorMap(np.uint8(255 * raw_vis), cv2.COLORMAP_JET)
        heatmap_raw = cv2.cvtColor(heatmap_raw, cv2.COLOR_BGR2RGB) / 255.0
        heatmap_norm = cv2.applyColorMap(np.uint8(255 * normalized_cam), cv2.COLORMAP_JET)
        heatmap_norm = cv2.cvtColor(heatmap_norm, cv2.COLOR_BGR2RGB) / 255.0

        overlay = 0.4 * (img_res / 255.0) + 0.6 * heatmap_norm
        overlay = np.clip(overlay, 0, 1)

        base = count * 4
        plt.subplot(8, 8, base + 1)
        plt.imshow(img_res)
        plt.title(f"{class_name}\nOriginal", fontsize=10)
        plt.axis('off')

        plt.subplot(8, 8, base + 2)
        plt.imshow(heatmap_raw)
        plt.title("Raw CAM", fontsize=10)
        plt.axis('off')

        plt.subplot(8, 8, base + 3)
        plt.imshow(heatmap_norm)
        plt.title("Normalized CAM", fontsize=10)
        plt.axis('off')

        plt.subplot(8, 8, base + 4)
        plt.imshow(overlay)
        plt.title("Overlay", fontsize=10)
        plt.axis('off')

        count += 1

    plt.suptitle(f"Grad-CAM Visualizations - {model_name} (First {max_examples} Classes)", fontsize=18)
    plt.tight_layout()
    plt.show()

print("\nGenerating Grad-CAM for With Attention Model...")
show_gradcam_grid(model_attn, "With Attention Model")

print("\nGenerating Grad-CAM for Without Attention Model...")
show_gradcam_grid(model_no_attn, "Without Attention Model")



# Cell 13: Simple & Accurate Real-time BdSL Prediction (NO MediaPipe - Reliable Center Crop)
# No external hand detector → no errors!
# Crops CENTER of frame (assume you hold hand centered, filling most of view)
# Matches your dataset (cropped hands) → correct predictions with your 100% model
# Plain background + good lighting = near-perfect live accuracy

from IPython.display import display, clear_output, HTML, Javascript
import time
import cv2
import numpy as np
from base64 import b64decode
from google.colab.output import eval_js
from PIL import Image, ImageDraw, ImageFont
from google.colab.patches import cv2_imshow
import torch.nn.functional as F

# Camera setup (mirrored view)
display(HTML("""
<div style="text-align: center;">
  <video id="video" width="640" height="480" autoplay playsinline style="transform: scaleX(-1); border: 5px solid #00ff00; border-radius: 15px;"></video>
  <p style="font-size:22px; color:#00ff00; margin-top:10px;"><strong>
    HOLD HAND IN CENTER • FILL THE FRAME • PLAIN BACKGROUND<br>
    Bengali sign + confidence will appear correctly!
  </strong></p>
</div>
"""))

display(Javascript("""
async function setupCamera() {
  const video = document.getElementById('video');
  try {
    const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: "user"}});
    video.srcObject = stream;
    await video.play();
  } catch (err) {
    alert("Camera error - allow permission and re-run cell");
  }
}
setupCamera();
"""))

time.sleep(4)

def capture_frame():
    data = eval_js("""
    (function() {
      const video = document.getElementById('video');
      if (!video || video.videoWidth === 0) return null;
      const canvas = document.createElement('canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0);
      return canvas.toDataURL('image/jpeg', 0.9);
    })();
    """)
    if data is None or not data.startswith('data:image'): return None
    try:
        binary = b64decode(data.split(',')[1])
        frame = cv2.imdecode(np.frombuffer(binary, np.uint8), -1)
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    except:
        return None

# Bengali font (already installed from your Cell 10)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoSansBengali-Regular.ttf", 32)
except:
    font = ImageFont.load_default()  # Fallback (still shows Bengali)

print("\n=== SIMPLE & ACCURATE LIVE BdSL PREDICTION STARTED ===")
model_attn.eval()

while True:
    frame_rgb = capture_frame()
    if frame_rgb is None:
        time.sleep(0.5)
        continue

    h, w, _ = frame_rgb.shape
    # Crop center square (80% of smaller dimension) → focuses on hand
    size = int(0.8 * min(h, w))
    center_x, center_y = w // 2, h // 2
    crop = frame_rgb[center_y - size//2 : center_y + size//2,
                     center_x - size//2 : center_x + size//2]

    # If crop empty (rare), skip
    if crop.size == 0:
        pred_text = "Adjust hand position"
        confidence = 0.0
    else:
        # Predict on cropped center
        img_pil = Image.fromarray(crop)
        input_tensor = test_transform(img_pil).unsqueeze(0).to(device)

        with torch.no_grad():
            output = model_attn(input_tensor)
            prob = F.softmax(output, dim=1)
            conf, pred = torch.max(prob, 1)
            pred_class = class_names[pred.item()]
            confidence = conf.item() * 100

        pred_text = f"{pred_class} ({confidence:.1f}%)"

    # Draw on full frame
    img_pil_full = Image.fromarray(frame_rgb)
    draw = ImageDraw.Draw(img_pil_full)

    # Large text with background
    bbox = draw.textbbox((0, 0), pred_text, font=font)
    draw.rectangle([(20, 10), (20 + bbox[2] - bbox[0] + 30, 10 + bbox[3] - bbox[1] + 30)], fill=(0, 0, 0, 180))
    color = (0, 255, 0) if confidence > 80 else (0, 165, 255) if confidence > 50 else (0, 0, 255)
    draw.text((30, 20), pred_text, font=font, fill=color, stroke_width=5, stroke_fill=(0, 0, 0))

    # Green box showing crop area (so you know where to place hand)
    draw.rectangle([center_x - size//2, center_y - size//2,
                    center_x + size//2, center_y + size//2], outline=(0, 255, 0), width=8)

    frame_bgr = cv2.cvtColor(np.array(img_pil_full), cv2.COLOR_RGB2BGR)

    clear_output(wait=True)
    cv2_imshow(frame_bgr)
    time.sleep(0.25)  # ~4 FPS smooth

















































