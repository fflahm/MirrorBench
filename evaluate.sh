#!/bin/bash
# evaluate.sh

if [ -z "$1" ]; then
    echo "Usage: $0 MODEL_NAME"
    exit 1
fi
model="$1"
echo "Using model: $model"
echo

bodies=("male_0" "male_1" "female_0" "female_1")
hands=("mano_white" "mano_brown" "mano_purple")
marks=("splash" "leaf_0" "leaf_1" "bread")

for l in 0 1 2 3; do
    for b in "${bodies[@]}"; do
        for h in "${hands[@]}"; do
            for m in "${marks[@]}"; do
                "$ISAACSIM_ROOT/python.bat" inference.py \
                    --body "$b" \
                    --hand "$h" \
                    --mark "$m" \
                    --level "$l" \
                    --model "$model" \
                    --headless
            done
        done
    done
done

bodies=("tienkung" "GR1_T2" "nova_carter")
hands=("allegro" "shadow_hand" "Robotiq_2F_85")
marks=("logo_0" "logo_1")

for l in 0 1 2 3; do
    for b in "${bodies[@]}"; do
        for h in "${hands[@]}"; do
            for m in "${marks[@]}"; do
                "$ISAACSIM_ROOT/python.bat" inference.py \
                    --body "$b" \
                    --hand "$h" \
                    --mark "$m" \
                    --level "$l" \
                    --model "$model" \
                    --headless
            done
        done
    done
done
